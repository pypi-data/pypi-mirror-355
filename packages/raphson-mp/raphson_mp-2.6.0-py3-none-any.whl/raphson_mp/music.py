from __future__ import annotations

import asyncio
import json
import logging
import random
import shutil
import tempfile
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from json.decoder import JSONDecodeError
from pathlib import Path
from sqlite3 import Connection

from aiohttp import web

from raphson_mp import (
    auth,
    cache,
    db,
    image,
    process,
    reddit,
    scanner,
    settings,
)
from raphson_mp.common import metadata
from raphson_mp.common.image import ImageFormat, ImageQuality
from raphson_mp.common.lyrics import Lyrics
from raphson_mp.common.lyrics import from_text as lyrics_from_text
from raphson_mp.common.track import AudioFormat, TrackBase

log = logging.getLogger(__name__)


# .wma is intentionally missing, ffmpeg support seems to be flaky
MUSIC_EXTENSIONS = [
    "mp3",
    "flac",
    "ogg",
    "webm",
    "mkv",
    "mka",
    "m4a",
    "wav",
    "opus",
    "mp4",
]

TRASH_PREFIX = ".trash."


def to_relpath(path: Path) -> str:
    """
    Returns: Relative path as string, excluding base music directory
    """
    relpath = path.as_posix()[len(settings.music_dir.as_posix()) + 1 :]
    return relpath if len(relpath) > 0 else ""


def from_relpath(relpath: str) -> Path:
    """
    Creates Path object from string path relative to music base directory, with directory
    traversal protection.
    """
    if relpath and (relpath[0] == "/" or relpath[-1] == "/"):
        raise ValueError("relpath must not start or end with slash: " + relpath)

    # resolve() is important for is_relative_to to work properly!
    path = Path(settings.music_dir, relpath).resolve()

    if not path.is_relative_to(settings.music_dir):
        raise ValueError(f"path {path.as_posix()} is not inside music base directory {settings.music_dir.as_posix()}")

    return path


def relpath_playlist(relpath: str):
    try:
        return relpath[: relpath.index("/")]
    except ValueError:
        return relpath


def is_trashed(path: Path) -> bool:
    """
    Returns: Whether this file or directory is trashed, by checking for the
    trash prefix in all path parts.
    """
    for part in path.parts:
        if part.startswith(TRASH_PREFIX):
            return True
    return False


def is_music_file(path: Path) -> bool:
    """
    Returns: Whether the provided path is a music file, by checking its extension
    """
    if not path.is_file():
        return False
    if is_trashed(path):
        return False
    for ext in MUSIC_EXTENSIONS:
        if path.name.endswith(ext):
            return True
    return False


def list_tracks_recursively(path: Path, trashed: bool = False) -> Iterator[Path]:
    """
    Scan directory for tracks, recursively
    Args:
        path: Directory Path
    Returns: Paths iterator
    """
    for ext in MUSIC_EXTENSIONS:
        for track_path in path.glob("**/*." + ext):
            if is_trashed(track_path) == trashed:
                yield track_path


async def _get_original_cover(artist: str | None, album: str, meme: bool):
    from raphson_mp import bing, musicbrainz

    log.debug("find cover for artist=%s album=%s", artist, album)

    if meme:
        if random.random() > 0.5:
            if image_bytes := await reddit.get_image(album):
                log.debug("returning reddit meme for artist=%s album=%s", artist, album)
                return cache.CacheData(image_bytes, cache.MONTH)

        for image_bytes in await bing.image_search(album + " meme"):
            log.debug("returning bing meme for artist=%s album=%s", artist, album)
            return cache.CacheData(image_bytes, cache.MONTH)

        log.debug("no meme found for artist=%s album=%s, try finding regular cover", artist, album)

    # Try MusicBrainz first
    if artist:
        if image_bytes := await musicbrainz.get_cover(artist, album):
            log.debug("returning musicbrainz cover for artist=%s album=%s", artist, album)
            return cache.CacheData(image_bytes, cache.HALFYEAR)

    if artist:
        query = artist + " - " + album
    else:
        query = album + " album cover art"

    # Otherwise try bing
    for image_bytes in await bing.image_search(query):
        log.debug("returning bing cover for artist=%s album=%s query=%s", artist, album, query)
        return cache.CacheData(image_bytes, cache.MONTH)

    log.debug("returning fallback raphson cover for artist=%s album=%s", artist, album)
    return cache.CacheData(settings.raphson_png.read_bytes(), cache.WEEK)


async def get_original_cover(artist: str | None, album: str, meme: bool) -> bytes:
    image_bytes = await cache.retrieve_or_store(f"cover{artist}{album}{meme}", _get_original_cover, artist, album, meme)
    if image_bytes:
        return image_bytes
    return settings.raphson_png.read_bytes()


async def _get_cover_thumbnail(
    artist: str | None,
    album: str,
    meme: bool,
    img_quality: ImageQuality,
    img_format: ImageFormat,
) -> cache.CacheData:
    original_bytes = await get_original_cover(artist, album, meme)

    log.debug(
        "transcoding cover to a thumbnail for artist=%s album=%s meme=%s img_quality=%s img_format=%s",
        artist,
        album,
        meme,
        img_quality,
        img_format,
    )

    with tempfile.TemporaryDirectory(prefix="music-cover") as temp_dir:
        input_path = Path(temp_dir, "input")
        input_path.write_bytes(original_bytes)
        output_path = Path(temp_dir, "output")

        try:
            await image.thumbnail(
                input_path,
                output_path,
                img_format,
                img_quality,
                square=not meme,
            )
        except process.ProcessReturnCodeError:
            log.warning("failed to generate thumbnail, is the image corrupt? artist=%s album=%s", artist, album)
            output_path = settings.raphson_png

        return cache.CacheData(output_path.read_bytes(), cache.MONTH)


class NoSuchTrackError(ValueError):
    pass


class Track(TrackBase):
    conn: Connection

    def __init__(self, conn: Connection, relpath: str):
        query = "SELECT mtime, ctime, duration, title, album, album_artist, track_number, year, video, lyrics FROM track WHERE path=?"
        row = conn.execute(query, (relpath,)).fetchone()
        if row is None:
            raise NoSuchTrackError("Missing track from database: " + relpath)

        mtime, ctime, duration, title, album, album_artist, track_number, year, video, lyrics = row

        rows = conn.execute("SELECT artist FROM track_artist WHERE track=?", (relpath,)).fetchall()
        artists = metadata.sort_artists([row[0] for row in rows], album_artist)

        rows = conn.execute("SELECT tag FROM track_tag WHERE track=?", (relpath,)).fetchall()
        tags = [row[0] for row in rows]

        self.conn = conn
        super().__init__(
            path=relpath,
            mtime=mtime,
            ctime=ctime,
            duration=duration,
            title=title,
            album=album,
            album_artist=album_artist,
            year=year,
            track_number=track_number,
            video=video,
            lyrics=lyrics,
            artists=artists,
            tags=tags,
        )

    @property
    def filepath(self) -> Path:
        return from_relpath(self.path)

    async def _get_loudnorm_filter(self) -> cache.CacheData:
        # First phase of 2-phase loudness normalization
        # http://k.ylo.ph/2016/04/04/loudnorm.html
        log.info("Measuring loudness: %s", self.path)
        # Annoyingly, loudnorm outputs to stderr instead of stdout. Disabling logging also
        # hides the loudnorm output, so we must parse loudnorm from the output.
        _stdout, stderr = await process.run_output(
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            self.filepath.as_posix(),
            "-map",
            "0:a",
            "-af",
            "loudnorm=print_format=json",
            "-f",
            "null",
            "/dev/null",
        )

        # Manually find the start of loudnorm info json
        try:
            meas_out = stderr.decode(encoding="utf-8")
        except UnicodeDecodeError:
            meas_out = stderr.decode(encoding="latin-1")
        start = meas_out.rindex("Parsed_loudnorm_0") + 37
        end = start + meas_out[start:].index("}") + 1
        json_text = meas_out[start:end]
        try:
            meas_json = json.loads(json_text)
        except JSONDecodeError as ex:
            log.error("Invalid json: %s", json_text)
            log.error("Original output: %s", meas_out)
            raise ex

        log.info("Measured integrated loudness: %s", meas_json["input_i"])

        if float(meas_json["input_i"]) > 0:
            log.warning(
                "Measured positive loudness. This should be impossible, but can happen "
                + "with input files containing out of range values. Need to use "
                + "single-pass loudnorm filter instead."
            )
            log.warning("Track: %s", self.path)
            loudnorm = settings.loudnorm_filter
        else:
            loudnorm = (
                f"{settings.loudnorm_filter}:"
                + f"measured_I={meas_json['input_i']}:"
                + f"measured_TP={meas_json['input_tp']}:"
                + f"measured_LRA={meas_json['input_lra']}:"
                + f"measured_thresh={meas_json['input_thresh']}:"
                + f"offset={meas_json['target_offset']}:"
                + "linear=true"
            )

        # Cache for a year, expensive to calculate and orphan entries take up very little space
        return cache.CacheData(loudnorm.encode(), cache.YEAR)

    async def get_loudnorm_filter(self) -> str:
        """Get ffmpeg loudnorm filter string"""
        cache_key = "loud3" + self.path + str(self.mtime)

        data = await cache.retrieve_or_store(cache_key, self._get_loudnorm_filter)
        return data.decode()

    async def _transcoded_audio(self, output_path: Path, audio_format: AudioFormat):
        loudnorm = await self.get_loudnorm_filter()

        log.info("Transcoding audio: %s", self.path)

        input_options = [
            "-map",
            "0:a",  # only keep audio
            "-map_metadata",
            "-1",
        ]  # discard metadata

        cover_temp_file = None  # for mp3 format only

        if audio_format in {AudioFormat.WEBM_OPUS_HIGH, AudioFormat.WEBM_OPUS_LOW}:
            bit_rate = "128k" if audio_format == AudioFormat.WEBM_OPUS_HIGH else "48k"
            audio_options = [
                "-f",
                "webm",
                "-c:a",
                "libopus",
                "-b:a",
                bit_rate,
                "-vbr",
                "on",
                # Higher frame duration offers better compression at the cost of latency
                "-frame_duration",
                "60",
                "-vn",
            ]  # remove video track (and album covers)
        elif audio_format is AudioFormat.MP3_WITH_METADATA:
            # https://trac.ffmpeg.org/wiki/Encode/MP3
            cover = await self.get_cover(False, ImageQuality.HIGH, img_format=ImageFormat.JPEG)
            # Write cover to temp file so ffmpeg can read it
            # cover_temp_file = tempfile.NamedTemporaryFile('wb')  # pylint: disable=consider-using-with
            cover_temp_file = open("/tmp/test", "wb")
            cover_temp_file.write(cover)

            input_options = [
                "-i",
                cover_temp_file.name,  # Add album cover
                "-map",
                "0:a",  # include audio stream from first input
                "-map",
                "1:0",  # include first stream from second input
                "-id3v2_version",
                "3",
                "-map_metadata",
                "-1",  # discard original metadata
                "-metadata:s:v",
                "title=Album cover",
                "-metadata:s:v",
                "comment=Cover (front)",
                *self.get_ffmpeg_options(),
            ]  # set new metadata

            audio_options = [
                "-f",
                "mp3",
                "-c:a",
                "libmp3lame",
                "-c:v",
                "copy",  # Leave cover as JPEG, don't re-encode as PNG
                "-q:a",
                "2",
            ]  # VBR 190kbps
        else:
            raise ValueError(audio_format)

        await process.run(
            "ffmpeg",
            "-y",  # overwriting file is required, because the created temp file already exists
            *settings.ffmpeg_flags(),
            "-i",
            self.filepath.as_posix(),
            *input_options,
            *audio_options,
            "-t",
            str(settings.track_max_duration_seconds),
            "-ac",
            "2",
            "-filter:a",
            loudnorm,
            output_path.as_posix(),
        )

        if cover_temp_file:
            cover_temp_file.close()

        # Audio for sure doesn't change so ideally we'd cache for longer, but that would mean
        # deleted tracks remain in the cache for longer as well.
        return cache.HALFYEAR

    async def transcoded_audio(self, audio_format: AudioFormat) -> web.StreamResponse:
        """
        Normalize and compress audio using ffmpeg
        Returns: Compressed audio bytes
        """
        return await cache.retrieve_or_store_response(
            f"audio{audio_format.value}{self.path}", audio_format.content_type, self._transcoded_audio, audio_format
        )

    async def get_cover(self, meme: bool, img_quality: ImageQuality, img_format: ImageFormat) -> bytes:
        """
        Find album cover using MusicBrainz or Bing.
        Parameters:
            meta: Track metadata
        Returns: Album cover image bytes, or None if MusicBrainz nor bing found an image.
        """
        if self.album and not metadata.album_is_compilation(self.album):
            search_album = self.album
        elif self.title:
            search_album = self.title
        else:
            search_album = self.display_title(show_album=False, show_year=False)

        search_artist = self.album_artist if self.album_artist else self.primary_artist

        return await cache.retrieve_or_store(
            f"coverthumb{search_artist}{search_album}{meme}{img_quality.value}{img_format.value}",
            _get_cover_thumbnail,
            search_artist,
            search_album,
            meme,
            img_quality,
            img_format,
        )

    async def get_lyrics(self) -> Lyrics | None:
        if self.lyrics:
            log.info("using lyrics from metadata")
            return lyrics_from_text("metadata", self.lyrics)

        from raphson_mp import lyrics

        artist = self.primary_artist
        if self.title and artist:
            return await lyrics.find(self.title, artist, self.album, self.duration)

        log.info("can't search for lyrics due to missing metadata")
        return None

    def get_ffmpeg_options(self, option: str = "-metadata") -> list[str]:
        def convert(value: str | int | list[str] | None):
            if value is None:
                return ""
            if type(value) == list:
                return metadata.join_meta_list(value)
            return str(value)

        metadata_options: list[str] = [
            option,
            "album=" + convert(self.album),
            option,
            "artist=" + convert(self.artists),
            option,
            "title=" + convert(self.title),
            option,
            "date=" + convert(self.year),
            option,
            "album_artist=" + convert(self.album_artist),
            option,
            "track=" + convert(self.track_number),
            option,
            "lyrics=" + convert(self.lyrics),
            option,
            "genre=" + convert(self.tags),
        ]
        # Remove alternate lyrics tags
        for tag in metadata.ALTERNATE_LYRICS_TAGS:
            metadata_options.extend((option, tag + "="))
        return metadata_options

    async def save(self):
        """
        Write metadata to file
        """
        original_extension = self.path[self.path.rindex(".") - 1 :]
        # ogg format seems to require setting metadata in stream instead of container
        metadata_flag = "-metadata:s" if original_extension == ".ogg" else "-metadata"
        with tempfile.NamedTemporaryFile(suffix=original_extension) as temp_file:
            await process.run(
                "ffmpeg",
                "-y",  # overwriting file is required, because the created temp file already exists
                "-hide_banner",
                "-nostats",
                "-loglevel",
                settings.ffmpeg_log_level,
                "-i",
                self.filepath.as_posix(),
                "-codec",
                "copy",
                *self.get_ffmpeg_options(metadata_flag),
                temp_file.name,
            )
            shutil.copy(temp_file.name, self.filepath)


def filter_tracks(
    conn: Connection,
    limit: int,
    offset: int,
    *,
    playlist: str | None = None,
    artist: str | None = None,
    tag: str | None = None,
    album_artist: str | None = None,
    album: str | None = None,
    year: int | None = None,
    has_metadata: bool | None = None,
    order: str | None = None,
):
    select_query = "SELECT path FROM track"
    where_query = "WHERE true"
    params: list[str | int] = []
    if playlist:
        where_query += " AND playlist = ?"
        params.append(playlist)

    if artist:
        select_query += " JOIN track_artist ON path = track"
        where_query += " AND artist = ?"
        params.append(artist)

    if tag:
        select_query += " JOIN track_tag ON path = track"
        where_query += " AND tag = ?"
        params.append(tag)

    if album_artist:
        where_query += " AND album_artist = ?"
        params.append(album_artist)

    if album:
        where_query += " AND album = ?"
        params.append(album)

    if year:
        where_query += " AND year = ?"
        params.append(year)

    if has_metadata:
        # Has at least metadata for: title, album, album artist, artists
        where_query += """
            AND title NOT NULL
            AND album NOT NULL
            AND album_artist NOT NULL
            AND EXISTS(SELECT artist FROM track_artist WHERE track = path)
            """

    if has_metadata is False:
        where_query += """ AND (
            title IS NULL
            OR album IS NULL
            OR album_artist IS NULL
            OR NOT EXISTS(SELECT artist FROM track_artist WHERE track = path)
            OR year IS NULL
            )"""

    order_query = "ORDER BY ctime ASC"  # oldest first
    if order:
        if order == "title":
            order_query = "ORDER BY title ASC"  # alphabetical order
        elif order == "ctime":
            order_query = "ORDER BY ctime DESC"  # most recent first
        elif order == "year":
            where_query += " AND YEAR IS NOT NULL"
            order_query = "ORDER BY year DESC "  # most recent first
        elif order == "random":
            order_query = "ORDER BY RANDOM()"
        else:
            log.warning("ignoring invalid order: %s", order)

    query = f"{select_query} {where_query} {order_query} LIMIT {limit} OFFSET {offset}"

    log.debug("filter: %s", query)

    result = conn.execute(query, params)
    return [Track(conn, relpath) for relpath, in result]


@dataclass
class PlaylistStats:
    name: str
    track_count: int
    total_duration: int
    mean_duration: int
    artist_count: int
    has_title_count: int
    has_album_count: int
    has_album_artist_count: int
    has_year_count: int
    has_artist_count: int
    has_tag_count: int
    most_recent_choice: int
    least_recent_choice: int
    most_recent_mtime: int

    def __init__(self, conn: Connection, name: str):
        self.name = name
        row = conn.execute(
            "SELECT COUNT(*), SUM(duration), AVG(duration) FROM track WHERE playlist=?",
            (name,),
        ).fetchone()
        self.track_count, self.total_duration, self.mean_duration = row

        row = conn.execute(
            """
            SELECT COUNT(DISTINCT artist)
            FROM track_artist JOIN track ON track.path=track
            WHERE playlist=?
            """,
            (name,),
        ).fetchone()
        (self.artist_count,) = row

        (
            self.has_title_count,
            self.has_album_count,
            self.has_album_artist_count,
            self.has_year_count,
            self.most_recent_choice,
            self.least_recent_choice,
            self.most_recent_mtime,
        ) = conn.execute(
            """
            SELECT SUM(title IS NOT NULL),
                    SUM(album IS NOT NULL),
                    SUM(album_artist IS NOT NULL),
                    SUM(year IS NOT NULL),
                    MAX(last_chosen),
                    MIN(last_chosen),
                    MAX(mtime)
            FROM track WHERE playlist=?
            """,
            (name,),
        ).fetchone()

        (self.has_artist_count,) = conn.execute(
            """
            SELECT COUNT(DISTINCT track)
            FROM track_artist JOIN track ON track.path = track
            WHERE playlist=?
            """,
            (name,),
        ).fetchone()

        (self.has_tag_count,) = conn.execute(
            """
            SELECT COUNT(DISTINCT track)
            FROM track_tag JOIN track ON track.path = track
            WHERE playlist=?
            """,
            (name,),
        ).fetchone()


class TagMode(Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass
class Playlist:
    conn: Connection
    name: str
    track_count: int

    @property
    def changed(self) -> datetime:
        return scanner.last_change(self.conn, self.name)

    @property
    def path(self) -> Path:
        return from_relpath(self.name)

    async def choose_track(
        self,
        user: auth.User | None,
        require_metadata: bool = False,
        tag_mode: TagMode | None = None,
        tags: list[str] | None = None,
    ) -> Track | None:
        """
        Randomly choose a track from this playlist
        Args:
            user: optionally specify a user to exclude tracks that this user has disliked
            require_metadata: only return tracks with at least some metadata (title, album, artists)
            tag_mode Tag mode (optional, must provide tags)
            tags: List of tags (optional, must provide tag_mode)
        Returns: Track object
        """
        # Select least recently played tracks
        query = "SELECT track.path, last_chosen FROM track WHERE playlist = ?"

        params: list[str | int] = [self.name]

        # don't choose disliked track
        if user is not None:
            query += " AND NOT EXISTS (SELECT 1 FROM dislikes WHERE user=? AND track=path)"
            params.append(user.user_id)

        # tags
        track_tags_query = "SELECT tag FROM track_tag WHERE track = track.path"
        if tag_mode is TagMode.ALLOW:
            assert tags is not None
            query += " AND (" + " OR ".join(len(tags) * [f"? IN ({track_tags_query})"]) + ")"
            params.extend(tags)
        elif tag_mode is TagMode.DENY:
            assert tags is not None
            query += " AND (" + " AND ".join(len(tags) * [f"? NOT IN ({track_tags_query})"]) + ")"
            params.extend(tags)

        # metadata is required for guessing game
        if require_metadata:
            # Has at least metadata for: title, album, artists
            query += (
                " AND title NOT NULL AND album NOT NULL AND EXISTS(SELECT artist FROM track_artist WHERE track = path)"
            )

        query += f" ORDER BY last_chosen ASC LIMIT {self.track_count // 4 + 1}"

        # From selected least recently played tracks, choose a random one
        query = "SELECT * FROM (" + query + ") ORDER BY RANDOM() LIMIT 1"

        row = self.conn.execute(query, params).fetchone()
        if row is None:
            # No track found
            return None

        track, last_chosen = row
        current_timestamp = int(time.time())
        if last_chosen == 0:
            log.info("Chosen track: %s (never played)", track)
        else:
            hours_ago = (current_timestamp - last_chosen) / 3600
            log.info("Chosen track: %s (last played %.2f hours ago)", track, hours_ago)

        # it would be nice if this could be done in the background with create_task(), but that would cause
        # duplicate tracks to be chosen at times when the next track is chosen before last_chosen is updated
        def update_last_chosen():
            with db.connect() as writable_conn:
                writable_conn.execute("UPDATE track SET last_chosen = ? WHERE path=?", (current_timestamp, track))

        await asyncio.to_thread(update_last_chosen)

        return Track(self.conn, track)

    def has_write_permission(self, user: auth.User) -> bool:
        """Check if user is allowed to modify files in a playlist."""
        if user.admin:
            return True

        row = self.conn.execute(
            "SELECT user FROM user_playlist_write WHERE playlist=? AND user=?",
            (self.name, user.user_id),
        ).fetchone()

        return row is not None

    def stats(self) -> PlaylistStats:
        """Get playlist statistics"""
        return PlaylistStats(self.conn, self.name)

    def tracks(self) -> list[Track]:
        """Get list of tracks in this playlist"""
        tracks: list[Track] = []
        for relpath in self.conn.execute("SELECT path FROM track WHERE playlist = ?", (self.name,)):
            tracks.append(Track(self.conn, relpath))
        return tracks

    @property
    def duration(self) -> int:
        duration = self.conn.execute("SELECT SUM(duration) FROM track WHERE playlist = ?", (self.name,)).fetchone()[0]
        return duration if duration else 0

    @staticmethod
    def from_path(conn: Connection, path: Path) -> Playlist:
        """
        Get parent playlist for a path
        Args:
            conn: Database connection
            path: Any (nested) path
        Returns: Playlist object
        """
        relpath = to_relpath(path)
        try:
            name = relpath[: relpath.index("/")]
        except ValueError:  # No slash found
            name = relpath
        relpath = to_relpath(path)
        return Playlist.by_name(conn, name)

    @staticmethod
    def by_name(conn: Connection, name: str) -> Playlist:
        track_count = conn.execute("SELECT COUNT(*) FROM track WHERE playlist=?", (name,)).fetchone()[0]
        return Playlist(conn, name, track_count)


@dataclass
class UserPlaylist(Playlist):
    write: bool
    favorite: bool


def playlist(conn: Connection, name: str) -> Playlist:
    """
    Get playlist by name
    Args:
        conn: Database connection
        name: Name of directory
    Returns: Playlist object
    """
    row = conn.execute(
        """
        SELECT (SELECT COUNT(*) FROM track WHERE playlist=playlist.name)
        FROM playlist
        WHERE name=?
        """,
        (name,),
    ).fetchone()
    (track_count,) = row
    return Playlist(conn, name, track_count)


def user_playlist(conn: Connection, name: str, user_id: int) -> UserPlaylist:
    """
    Get playlist by name, with user-specific information
    Args:
        conn: Database connection
        name: Playlist name
        user_id
    Returns: UserPlaylist object
    """
    row = conn.execute(
        """
        SELECT (SELECT COUNT(*) FROM track WHERE playlist=name),
                EXISTS(SELECT 1 FROM user_playlist_write WHERE playlist=name AND user=:user) AS write,
                EXISTS(SELECT 1 FROM user_playlist_favorite WHERE playlist=name AND user=:user) AS favorite
        FROM playlist
        WHERE name=:playlist
        """,
        {"user": user_id, "playlist": name},
    ).fetchone()
    track_count, write, favorite = row
    return UserPlaylist(conn, name, track_count, write == 1, favorite == 1)


def playlists(conn: Connection) -> list[Playlist]:
    """
    List playlists
    Returns: List of Playlist objects
    """
    rows = conn.execute(
        """
        SELECT name, (SELECT COUNT(*) FROM track WHERE playlist=playlist.name)
        FROM playlist
        """
    )
    return [Playlist(conn, name, track_count) for name, track_count in rows]


def user_playlists(conn: Connection, user_id: int, all_writable: bool = False) -> list[UserPlaylist]:
    """
    List playlists, with user-specific information
    Args:
        conn: Database connection
        user_id
        all_writable: True if all playlists must be treated as writable. Useful in some cases if the user is an administrator.
    Returns: List of UserPlaylist objects
    """
    rows = conn.execute(
        """
        SELECT name,
                (SELECT COUNT(*) FROM track WHERE playlist=playlist.name),
                EXISTS(SELECT 1 FROM user_playlist_write WHERE playlist=name AND user=:user) AS write,
                EXISTS(SELECT 1 FROM user_playlist_favorite WHERE playlist=name AND user=:user) AS favorite
        FROM playlist
        ORDER BY favorite DESC, name COLLATE NOCASE ASC
        """,
        {"user": user_id},
    )

    return [
        UserPlaylist(
            conn,
            name,
            track_count,
            write == 1 or all_writable,
            favorite == 1,
        )
        for name, track_count, write, favorite in rows
    ]
