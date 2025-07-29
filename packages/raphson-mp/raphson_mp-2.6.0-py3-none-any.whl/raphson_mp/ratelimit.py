import asyncio
from types import TracebackType

from raphson_mp import settings


class RateLimitError(Exception):
    pass


class RateLimiter:
    time: float
    abort: bool
    lock: asyncio.Lock | None = None
    release_task: asyncio.Task[None] | None = None

    def __init__(self, time: float, abort: bool = False):
        self.time = time
        self.abort = abort

    async def __aenter__(self):
        if settings.server is None:
            return

        if not self.lock:
            self.lock = asyncio.Lock()

        if self.abort and self.lock.locked():
            raise RateLimitError

        await self.lock.acquire()

    async def __aexit__(self, _exc_type: type[Exception], _exc_value: Exception, _exc_tb: TracebackType):
        # During testing, different event loops are used so a lock can't be used.
        # Instead, just sleep always. Tests will take longer, but that's fine.
        if settings.server is None:
            await asyncio.sleep(self.time)
            return

        async def release_later():
            assert self.lock
            await asyncio.sleep(self.time)
            self.lock.release()
            self.release_task = None

        self.release_task = asyncio.create_task(release_later())


MUSICBRAINZ = RateLimiter(1)
LASTFM = RateLimiter(0.5)
ACOUSTID = RateLimiter(0.5)
REDDIT = RateLimiter(6)
ERROR_REPORT = RateLimiter(5)
