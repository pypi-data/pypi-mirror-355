from sqlite3 import Connection

from aiohttp import web

from raphson_mp import charts
from raphson_mp.auth import User
from raphson_mp.charts import StatsPeriod
from raphson_mp.decorators import route
from raphson_mp.response import template


@route("", redirect_to_login=True)
async def route_stats(_request: web.Request, _conn: Connection, _user: User):
    return await template("stats.jinja2", chart_count=len(charts.CHARTS))


@route("/data/{chart}")
async def route_stats_data(request: web.Request, _conn: Connection, _user: User):
    period = StatsPeriod.from_str(request.query["period"])
    chart_id = int(request.match_info["chart"])
    data = await charts.get_chart(chart_id, period)
    if data is None:
        raise web.HTTPNoContent(reason="not enough data")
    return web.json_response(data)
