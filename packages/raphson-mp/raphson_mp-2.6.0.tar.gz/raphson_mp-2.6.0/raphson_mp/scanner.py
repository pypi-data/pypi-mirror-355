from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from sqlite3 import Connection

from raphson_mp import db, event, music, settings
from raphson_mp.auth import User
from raphson_mp.common import metadata
from raphson_mp.common.control import FileAction
from raphson_mp.util import log_duration

log = logging.getLogger(__name__)

SCANNER_LOCK = threading.Lock()


class Counter:
    count: int = 0


def _scan_playlists(conn: Connection) -> list[music.Playlist]:
    """
    Scan playlist directories, add or remove playlists from the database
    where necessary.
    """
    names_db = {row[0] for row in conn.execute("SELECT name FROM playlist")}
    paths_disk = [path for path in settings.music_dir.iterdir() if path.is_dir() and not music.is_trashed(path)]
    names_disk = {path.name for path in paths_disk}

    add_to_db: list[tuple[str]] = []
    remove_from_db: list[tuple[str]] = []

    for name in names_db:
        if name not in names_disk:
            log.info("Going to delete playlist: %s", name)
            remove_from_db.append((name,))

    for name in names_disk:
        if name not in names_db:
            log.info("New playlist: %s", name)
            add_to_db.append((name,))

    if add_to_db:
        conn.executemany("INSERT INTO playlist (name) VALUES (?)", add_to_db)
    if remove_from_db:
        conn.executemany("DELETE FROM playlist WHERE name=?", remove_from_db)

    return [music.Playlist(conn, name, -1) for name in names_disk]


async def scan_playlists():
    def thread():
        with SCANNER_LOCK:
            with db.connect() as conn:
                _scan_playlists(conn)

    await asyncio.to_thread(thread)


@dataclass
class QueryParams:
    main_data: dict[str, str | int | None]
    artist_data: list[dict[str, str]]
    tag_data: list[dict[str, str]]


def query_params(relpath: str, path: Path) -> QueryParams | None:
    """
    Create cdictionary of track metadata, to be used as SQL query parameters
    """
    try:
        stdout = subprocess.check_output(
            ["ffprobe", "-show_streams", "-show_format", "-print_format", "json", path.as_posix()],
        )
    except subprocess.CalledProcessError:
        log.warning("Error scanning track %s, is it corrupt?", path)
        return None

    data = json.loads(stdout.decode())

    if "duration" not in data["format"]:
        # static image
        return None

    duration = int(float(data["format"]["duration"]))
    artists: list[str] = []
    album: str | None = None
    title: str | None = None
    year: int | None = None
    album_artist: str | None = None
    track_number: int | None = None
    tags: list[str] = []
    lyrics: str | None = None
    video: str | None = None

    meta_tags: list[tuple[str, str]] = []

    for stream in data["streams"]:
        if stream["codec_type"] == "audio":
            if "tags" in stream:
                meta_tags.extend(stream["tags"].items())

        if stream["codec_type"] == "video":
            if stream["codec_name"] == "vp9":
                video = "vp9"
            elif stream["codec_name"] == "h264":
                video = "h264"

    if "tags" in data["format"]:
        meta_tags.extend(data["format"]["tags"].items())

    for name, value in meta_tags:
        # sometimes ffprobe returns tags in uppercase
        name = name.lower()

        if metadata.has_advertisement(value):
            log.info("Ignoring advertisement: %s = %s", name, value)
            continue

        # replace weird quotes by normal quotes
        value = value.replace("’", "'").replace("`", "'")

        if name == "album":
            album = value

        if name == "artist":
            artists = metadata.split_meta_list(value)

        if name == "title":
            title = metadata.strip_keywords(value).strip()

        if name == "date":
            try:
                year = int(value[:4])
            except ValueError:
                log.warning("Invalid year '%s' in file '%s'", value, path.resolve().as_posix())

        if name == "album_artist":
            album_artist = value

        if name == "track":
            try:
                track_number = int(value.split("/")[0])
            except ValueError:
                log.warning(
                    "Invalid track number '%s' in file '%s'",
                    value,
                    path.resolve().as_posix(),
                )

        if name == "genre":
            tags = metadata.split_meta_list(value)

        if name == "lyrics":
            lyrics = value

        # Allow other lyrics tags, but only if no other lyrics are available
        if name in metadata.ALTERNATE_LYRICS_TAGS and lyrics is None:
            lyrics = value

    main_data: dict[str, str | int | None] = {
        "path": relpath,
        "duration": duration,
        "title": title,
        "album": album,
        "album_artist": album_artist,
        "track_number": track_number,
        "year": year,
        "lyrics": lyrics,
        "video": video,
    }
    artist_data = [{"track": relpath, "artist": artist} for artist in artists]
    tag_data = [{"track": relpath, "tag": tag} for tag in tags]

    return QueryParams(main_data, artist_data, tag_data)


def _scan_track(
    loop: asyncio.AbstractEventLoop,
    conn: Connection,
    user: User | None,
    playlist: str,
    track_path: Path,
    track_relpath: str,
) -> bool:
    """
    Scan single track.
    Returns: Whether track exists (False if deleted)
    """
    if not music.is_music_file(track_path):
        if conn.execute("SELECT 1 FROM track WHERE path = ?", (track_relpath,)).fetchone() is None:
            # track already doesn't exist
            return False

        log.info("Deleted: %s", track_relpath)
        conn.execute("DELETE FROM track WHERE path=?", (track_relpath,))
        _log(loop, conn, event.FileChangeEvent(FileAction.DELETE, track_relpath, user))
        return False

    row = conn.execute("SELECT mtime FROM track WHERE path=?", (track_relpath,)).fetchone()
    db_mtime = row[0] if row else None
    file_mtime = int(track_path.stat().st_mtime)

    # Track does not yet exist in database
    if db_mtime is None:
        log.info("New track, insert: %s", track_relpath)
        params = query_params(track_relpath, track_path)
        if not params:
            return False

        conn.execute("BEGIN")
        conn.execute(
            """
            INSERT INTO track (path, playlist, duration, title, album, album_artist, track_number, year, lyrics, video, mtime, ctime)
            VALUES (:path, :playlist, :duration, :title, :album, :album_artist, :track_number, :year, :lyrics, :video, :mtime, :ctime)
            """,
            {**params.main_data, "playlist": playlist, "mtime": file_mtime, "ctime": int(time.time())},
        )
        conn.executemany("INSERT INTO track_artist (track, artist) VALUES (:track, :artist)", params.artist_data)
        conn.executemany("INSERT INTO track_tag (track, tag) VALUES (:track, :tag)", params.tag_data)
        conn.execute("COMMIT")

        _log(loop, conn, event.FileChangeEvent(FileAction.INSERT, track_relpath, user))
        return True

    if file_mtime != db_mtime:
        log.info(
            "Changed, update: %s (%s to %s)",
            track_relpath,
            datetime.fromtimestamp(db_mtime, tz=timezone.utc),
            datetime.fromtimestamp(file_mtime, tz=timezone.utc),
        )
        params = query_params(track_relpath, track_path)
        if not params:
            log.warning("Metadata error, delete track from database")
            conn.execute("DELETE FROM track WHERE path=?", (track_relpath,))
            _log(loop, conn, event.FileChangeEvent(FileAction.DELETE, track_relpath, user))
            return False

        conn.execute("BEGIN")
        conn.execute(
            """
            UPDATE track
            SET duration=:duration,
                title=:title,
                album=:album,
                album_artist=:album_artist,
                track_number=:track_number,
                year=:year,
                lyrics=:lyrics,
                video=:video,
                mtime=:mtime
            WHERE path=:path
            """,
            {**params.main_data, "mtime": file_mtime},
        )
        conn.execute("DELETE FROM track_artist WHERE track=?", (track_relpath,))
        conn.executemany("INSERT INTO track_artist (track, artist) VALUES (:track, :artist)", params.artist_data)
        conn.execute("DELETE FROM track_tag WHERE track=?", (track_relpath,))
        conn.executemany("INSERT INTO track_tag (track, tag) VALUES (:track, :tag)", params.tag_data)
        conn.execute("COMMIT")

        _log(loop, conn, event.FileChangeEvent(FileAction.UPDATE, track_relpath, user))
        return True

    # Track exists in filesystem and is unchanged
    return True


def _scan_playlist(
    loop: asyncio.AbstractEventLoop,
    conn: Connection,
    user: User | None,
    playlist: music.Playlist,
    counter: Counter | None,
) -> None:
    """
    Scan for added, removed or changed tracks in a playlist.
    """
    log.info("Scanning playlist: %s", playlist.name)
    paths_db: set[str] = set()
    with log_duration("scan existing tracks"):
        for (track_relpath,) in conn.execute("SELECT path FROM track WHERE playlist=?", (playlist.name,)).fetchall():
            if counter:
                counter.count += 1
            if _scan_track(loop, conn, user, playlist.name, music.from_relpath(track_relpath), track_relpath):
                paths_db.add(track_relpath)

    with log_duration("scan new tracks"):
        for track_path in music.list_tracks_recursively(playlist.path):
            track_relpath = music.to_relpath(track_path)
            if track_relpath not in paths_db:
                if counter:
                    counter.count += 1
                _scan_track(loop, conn, user, playlist.name, track_path, track_relpath)


async def scan_playlist(user: User | None, playlist: music.Playlist) -> None:
    """
    Scan for added, removed or changed tracks in a playlist.
    Returns: number of changes
    """
    loop = asyncio.get_running_loop()

    def thread():
        with SCANNER_LOCK:
            with db.connect() as conn:
                _scan_playlist(loop, conn, user, playlist, None)

    await asyncio.to_thread(thread)


async def scan_track(user: User | None, path: Path) -> None:
    """
    Scan single track for changes
    """
    loop = asyncio.get_running_loop()

    def thread():
        relpath = music.to_relpath(path)
        with SCANNER_LOCK:
            with db.connect() as conn:
                _scan_track(loop, conn, user, music.relpath_playlist(relpath), path, relpath)

    await asyncio.to_thread(thread)


async def move(user: User, from_path: Path, to_path: Path):
    loop = asyncio.get_running_loop()

    def thread():
        from_relpath = music.to_relpath(from_path)
        to_relpath = music.to_relpath(to_path)
        from_playlist = music.relpath_playlist(from_relpath)
        to_playlist = music.relpath_playlist(to_relpath)
        was_music_file = music.is_music_file(from_path)
        from_path.rename(to_path)
        is_music_file = music.is_music_file(to_path)
        with db.connect() as conn:
            # The file was renamed to add or remove a music extension, or trashed. It should be scanned to add or remove the track.
            if was_music_file != is_music_file:
                with SCANNER_LOCK:
                    _scan_track(loop, conn, user, from_playlist, from_path, from_relpath)
                    _scan_track(loop, conn, user, to_playlist, to_path, to_relpath)
                    return

            try:
                if to_path.is_dir():
                    # need to update all children of this directory
                    conn.execute("BEGIN")
                    for (change_relpath,) in conn.execute(
                        "SELECT path FROM track WHERE path LIKE ?", (from_relpath + "/%",)
                    ).fetchall():
                        new_relpath = to_relpath + change_relpath[len(from_relpath) :]
                        log.debug("track in directory has moved from %s to %s", change_relpath, new_relpath)
                        conn.execute(
                            "UPDATE track SET path = ?, playlist = ? WHERE path = ?",
                            (new_relpath, to_playlist, change_relpath),
                        )
                        _log(loop, conn, event.FileChangeEvent(FileAction.MOVE, new_relpath, user))
                    conn.execute("COMMIT")
                    return

                # the file might not be in the db, if it's not a music file or if it hasn't been scanned yet
                in_db = conn.execute("SELECT 1 FROM track WHERE path = ?", (from_relpath,)).fetchone() is not None
                if in_db:
                    conn.execute(
                        "UPDATE track SET path = ?, playlist = ? WHERE path = ?",
                        (to_relpath, to_playlist, from_relpath),
                    )
                    _log(loop, conn, event.FileChangeEvent(FileAction.MOVE, to_relpath, user))
            except Exception as ex:
                # if this somehow went wrong, attempt to rename the track back before raising the exception again
                to_path.rename(from_path)
                raise ex

    await asyncio.to_thread(thread)


def last_change(conn: Connection, playlist: str | None) -> datetime:
    if playlist is not None:
        query = "SELECT MAX(mtime) FROM track WHERE playlist = ?"
        params = (playlist,)
    else:
        query = "SELECT MAX(mtime) FROM track"
        params = ()
    (mtime,) = conn.execute(query, params).fetchone()
    if mtime is None:
        mtime = 0

    return datetime.fromtimestamp(mtime, timezone.utc)


async def scan(user: User | None, counter: Counter | None = None) -> None:
    """
    Main function for scanning music directory structure
    """
    if settings.offline_mode:
        log.info("Skip scanner in offline mode")
        return

    loop = asyncio.get_running_loop()

    def thread():
        with SCANNER_LOCK:
            with db.connect() as conn:
                playlists = _scan_playlists(conn)
                for playlist in playlists:
                    _scan_playlist(loop, conn, user, playlist, counter)

    await asyncio.to_thread(thread)


def _log(loop: asyncio.AbstractEventLoop, conn: Connection, ev: event.FileChangeEvent):
    asyncio.run_coroutine_threadsafe(event.fire(ev), loop)
    playlist_name = ev.track[: ev.track.index("/")]
    user_id = ev.user.user_id if ev.user else None

    conn.execute(
        """
        INSERT INTO scanner_log (timestamp, action, playlist, track, user)
        VALUES (?, ?, ?, ?, ?)
        """,
        (int(time.time()), ev.action.value, playlist_name, ev.track, user_id),
    )
