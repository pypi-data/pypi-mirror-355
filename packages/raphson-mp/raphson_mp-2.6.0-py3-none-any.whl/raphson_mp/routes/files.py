import asyncio
from pathlib import Path
from sqlite3 import Connection
from typing import cast

from aiohttp import web

from raphson_mp import auth, db, music, scanner, settings, util
from raphson_mp.auth import User
from raphson_mp.decorators import route
from raphson_mp.music import TRASH_PREFIX, Playlist
from raphson_mp.response import directory_as_zip, file_attachment, template
from raphson_mp.util import urlencode


def _get_files_url(path: Path):
    if path == settings.music_dir:
        return "/files"
    else:
        return "/files?path=" + util.urlencode(music.to_relpath(path))


@route("", redirect_to_login=True)
async def route_files(request: web.Request, conn: Connection, user: User):
    """
    File manager
    """
    path = request.query.get("path", ".")
    browse_path = music.from_relpath(path)

    show_trashed = "trash" in request.query

    if browse_path == settings.music_dir:
        back_url = "/"
        write_permission = user.admin
    else:
        back_url = _get_files_url(browse_path.parent)
        # If the base directory is writable, all paths inside it will be, too.
        playlist = Playlist.from_path(conn, browse_path)
        write_permission = playlist.has_write_permission(user)

    children: list[dict[str, str]] = []

    # iterdir() is slow and blocking, so must be run in a separate thread
    def thread():
        for path in browse_path.iterdir():
            if music.is_trashed(path) != show_trashed:
                continue

            relpath = music.to_relpath(path)

            children.append(
                {
                    "path": relpath,
                    "displayname": path.name[len(TRASH_PREFIX):] if show_trashed else path.name,
                    "type": "d" if path.is_dir() else "f",
                }
            )

    await asyncio.to_thread(thread)

    # go back to main thread to use database connection
    for child in children:
        if child["type"] == "dir":
            continue

        row = conn.execute(
            """
            SELECT title, GROUP_CONCAT(artist, ", ")
            FROM track LEFT JOIN track_artist ON path = track
            WHERE path = ?
            GROUP BY path
            """,
            (child["path"],),
        ).fetchone()

        if row:
            title, artists = row
            child["type"] = "m"
            child["title"] = title if title else ""
            child["artist"] = artists if artists else ""

    # Sort directories first, and ignore case for file name
    def sort_name(obj: dict[str, str]) -> str:
        return ("a" if obj["type"] == "d" else "b") + obj["displayname"].lower()

    children = sorted(children, key=sort_name)

    return await template(
        "files.jinja2",
        base_path=music.to_relpath(browse_path),
        base_url=_get_files_url(browse_path),
        back_url=back_url,
        write_permission=write_permission,
        files=children,
        music_extensions=",".join(music.MUSIC_EXTENSIONS),
        show_trashed=show_trashed,
    )


@route("/upload", method="POST")
async def route_upload(request: web.Request, conn: Connection, user: User):
    """
    Form target to upload file, called from file manager
    """
    form = await request.post()

    upload_dir = music.from_relpath(cast(str, form["dir"]))

    playlist = Playlist.from_path(conn, upload_dir)
    if not playlist.has_write_permission(user):
        raise web.HTTPForbidden(reason="No write permission for this playlist")

    def accept_files():
        for uploaded_file in cast(list[web.FileField], form.getall("upload")):
            util.check_filename(uploaded_file.filename)
            path = Path(upload_dir, uploaded_file.filename)
            with path.open("wb") as fp:
                while data := uploaded_file.file.read(16 * 1024 * 1024):
                    fp.write(data)

    await asyncio.to_thread(accept_files)

    await util.create_task(scanner.scan_playlist(user, playlist))

    raise web.HTTPSeeOther(_get_files_url(upload_dir))


@route("/rename")
async def route_rename_get(request: web.Request, _conn: Connection, _user: User):
    path = request.query["path"]
    back_url = _get_files_url(music.from_relpath(path).parent)
    return await template("files_rename.jinja2", path=path, name=path.split("/")[-1], back_url=back_url)


@route("/rename", method="POST")
async def route_rename_post(request: web.Request, conn: Connection, user: User):
    if request.content_type == "application/json":
        json = await request.json()
        relpath = cast(str, json["path"])
        new_name = cast(str, json["new_name"])
    else:
        form = await request.post()
        relpath = cast(str, form["path"])
        new_name = cast(str, form["new-name"])

    path = music.from_relpath(relpath)
    util.check_filename(new_name)

    playlist = Playlist.from_path(conn, path)
    if not playlist.has_write_permission(user):
        raise web.HTTPForbidden(reason="No write permission for this playlist")

    new_path = Path(path.parent, new_name)
    await scanner.move(user, path, new_path)

    if request.content_type == "application/json":
        raise web.HTTPNoContent()

    raise web.HTTPSeeOther(_get_files_url(path.parent))


@route("/mkdir", method="POST")
async def route_mkdir(request: web.Request, conn: Connection, user: auth.User):
    """
    Create directory, then enter it
    """
    form = await request.post()
    relpath = cast(str, form["path"])
    dirname = cast(str, form["dirname"])

    util.check_filename(dirname)
    parent = music.from_relpath(relpath)

    if relpath == "":
        to_create = Path(parent, dirname)

        # Creating a root playlist directory
        if to_create.exists():
            raise web.HTTPBadRequest(reason="Playlist path already exists")

        to_create.mkdir()

        # This creates a row for the playlist in the playlist table
        await scanner.scan_playlists()

        # New playlist should be writable for user who created it
        with db.connect() as writable_conn:
            writable_conn.execute("INSERT INTO user_playlist_write VALUES (?, ?)", (user.user_id, dirname))
    else:
        # Creating a directory inside an existing playlist
        playlist = Playlist.from_path(conn, parent)
        if not playlist.has_write_permission(user):
            raise web.HTTPForbidden(reason="No write permission for this playlist")

        to_create = Path(parent, dirname)
        to_create.mkdir()

    raise web.HTTPSeeOther("/files?path=" + urlencode(music.to_relpath(to_create)))


@route("/download")
async def route_download(request: web.Request, _conn: Connection, _user: User):
    """
    Download single file
    """
    path = music.from_relpath(request.query["path"])
    if path.is_dir():
        return directory_as_zip(path)

    if path.is_file():
        return file_attachment(path)

    raise web.HTTPBadRequest()
