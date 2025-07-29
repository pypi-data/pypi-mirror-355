import asyncio
from sqlite3 import Connection

from aiohttp import web
from raphson_mp.auth import User
from raphson_mp.decorators import route
from raphson_mp.music import Track
from raphson_mp.response import template
from raphson_mp import db


@route("")
async def problems(_request: web.Request, conn: Connection, _user: User):
    tracks = [Track(conn, row[0]) for row in conn.execute("SELECT track FROM track_problem")]
    return await template("problems.jinja2", tracks=tracks)


@route("/undo", method="POST")
async def undo(request: web.Request, _conn: Connection, _user: User):
    relpath = (await request.post())["path"]

    def thread():
        with db.connect() as writable_conn:
            writable_conn.execute("DELETE FROM track_problem WHERE track = ?", (relpath,))

    await asyncio.to_thread(thread)
    raise web.HTTPSeeOther("/problems")
