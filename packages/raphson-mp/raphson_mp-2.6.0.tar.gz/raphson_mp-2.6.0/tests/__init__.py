import asyncio
import secrets
from pathlib import Path

from aiohttp import web
from aiohttp.test_utils import TestClient

from raphson_mp import auth, db, logconfig, settings

T_client = TestClient[web.Request, web.Application]

TEST_USERNAME: str = "autotest"
TEST_PASSWORD: str = secrets.token_urlsafe()


def set_dirs():
    settings.data_dir = Path("./data").resolve()
    settings.music_dir = Path("./music").resolve()


def setup_module():
    set_dirs()
    settings.log_warnings_to_file = True
    settings.log_level = "DEBUG"
    logconfig.apply()

    with db.connect() as conn:
        conn.execute("DELETE FROM user WHERE username = ?", (TEST_USERNAME,))

    asyncio.run(auth.User.create(TEST_USERNAME, TEST_PASSWORD))


async def get_csrf(client: T_client):
    async with client.get("/auth/get_csrf") as response:
        assert response.status == 200, await response.text()
        return (await response.json())["token"]
