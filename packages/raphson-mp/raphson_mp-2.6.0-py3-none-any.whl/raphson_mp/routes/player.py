import asyncio
import shutil
from sqlite3 import Connection
from typing import cast

from aiohttp import web

from raphson_mp import music, scanner, util
from raphson_mp.auth import StandardUser, User
from raphson_mp.decorators import route
from raphson_mp.music import NoSuchTrackError, Track
from raphson_mp.response import template


@route("", redirect_to_login=True)
async def route_player(request: web.Request, _conn: Connection, user: User):
    """
    Main player page. Serves player.jinja2 template file.
    """
    response = await template(
        "player.jinja2",
        mobile=util.is_mobile(request),
        primary_playlist=user.primary_playlist,
    )

    # Refresh token cookie
    if isinstance(user, StandardUser):
        assert user.session
        user.session.set_cookie(response)

    return response


@route("/copy_track", method="POST")
async def route_copy_track(request: web.Request, conn: Connection, user: User):
    """
    Endpoint used by music player to copy a track to the user's primary playlist
    """
    json = await request.json()
    playlist_name = cast(str, json["playlist"])

    playlist = music.user_playlist(conn, playlist_name, user.user_id)
    if not user.admin and not playlist.write:
        raise web.HTTPForbidden(reason="no write access")

    try:
        track = Track(conn, cast(str, json["track"]))
    except NoSuchTrackError:
        raise web.HTTPBadRequest(reason="track does not exist")

    if track.playlist == playlist.name:
        raise web.HTTPBadRequest(reason="track already in playlist")

    await asyncio.to_thread(shutil.copy, track.filepath, playlist.path)

    asyncio.create_task(scanner.scan_playlist(user, playlist))

    raise web.HTTPNoContent()
