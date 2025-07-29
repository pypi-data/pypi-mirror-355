from aiohttp import web

from raphson_mp import settings
from raphson_mp.decorators import Route


static = Route([web.static("/", settings.static_dir)])
