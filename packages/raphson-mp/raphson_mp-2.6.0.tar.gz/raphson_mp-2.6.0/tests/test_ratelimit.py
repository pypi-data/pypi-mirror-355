import math
import time

from raphson_mp import ratelimit, settings
from raphson_mp.server import Server


async def test_ratelimit_standard():
    settings.server = Server(False, mock=True)

    start_time = time.time()
    limiter = ratelimit.RateLimiter(1)

    # first invocation should process instantly
    async with limiter:
        pass
    assert math.isclose(time.time() - start_time, 0, abs_tol=0.1)
    assert limiter.lock is not None

    # second invocation should start 1 second later
    async with limiter:
        assert math.isclose(time.time() - start_time, 1, abs_tol=0.1)
        pass
    assert math.isclose(time.time() - start_time, 1, abs_tol=0.1)

    if limiter.release_task:
        await limiter.release_task

    settings.server = None


async def test_ratelimit_testing_mode():
    start_time = time.time()
    limiter = ratelimit.RateLimiter(1)
    # in testing mode, the rate limiter should sleep
    async with limiter:
        pass
    assert math.isclose(time.time() - start_time, 1, abs_tol=0.1)

    # and it should not create a task
    async with limiter:
        assert not limiter.release_task
        pass
