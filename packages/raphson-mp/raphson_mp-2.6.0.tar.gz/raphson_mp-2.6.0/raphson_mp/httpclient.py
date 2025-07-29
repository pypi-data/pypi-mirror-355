from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, ParamSpec

import aiohttp

from raphson_mp import settings

_cached_connector: aiohttp.TCPConnector | None = None


async def close():
    global _cached_connector
    assert _cached_connector
    await _cached_connector.close()
    _cached_connector = None


P = ParamSpec("P")


@asynccontextmanager
async def session(
    base_url: str | None = None, scraping: bool = False, **kwargs: Any
) -> AsyncIterator[aiohttp.ClientSession]:
    kwargs.setdefault("raise_for_status", True)
    kwargs.setdefault("timeout", aiohttp.ClientTimeout(total=10, connect=5, sock_connect=5))

    user_agent = settings.webscraping_user_agent if scraping else settings.user_agent
    if "headers" in kwargs:
        kwargs["headers"].setdefault("User-Agent", user_agent)
    else:
        kwargs.setdefault("headers", {"User-Agent": user_agent})

    global _cached_connector
    if settings.server:
        if _cached_connector is None:
            _cached_connector = aiohttp.TCPConnector()
            settings.server.cleanup.append(close)

        kwargs.setdefault("connector", _cached_connector)
        kwargs.setdefault("connector_owner", False)

    session = aiohttp.ClientSession(base_url, **kwargs)
    try:
        yield session
    finally:
        await session.close()
