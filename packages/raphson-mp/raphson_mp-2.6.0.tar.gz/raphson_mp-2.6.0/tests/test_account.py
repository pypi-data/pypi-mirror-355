import random

from aiohttp import web

from raphson_mp import db, i18n, music, theme
from raphson_mp.auth import PrivacyOption

from . import TEST_PASSWORD, TEST_USERNAME, T_client, get_csrf


async def test_account_page(client: T_client):
    async with client.get("/account") as response:
        response.raise_for_status()


async def test_change_settings(client: T_client):
    with db.connect(read_only=True) as conn:
        data: dict[str, str | PrivacyOption | None] = {
            "csrf": await get_csrf(client),
            "nickname": random.choice(random.randbytes(4).hex()),
            "language": random.choice(list(i18n.ALL_LANGUAGE_CODES)),
            "privacy": random.choice([PrivacyOption.AGGREGATE, PrivacyOption.HIDDEN]).value,
            "playlist": random.choice([pl.name for pl in music.playlists(conn)]),
            "theme": random.choice(list(theme.THEMES)),
        }
        async with client.post("/account/change_settings", data=data) as response:
            response.raise_for_status()

        row = conn.execute(
            "SELECT nickname, language, privacy, primary_playlist, theme FROM user WHERE username=?", (TEST_USERNAME,)
        ).fetchone()
        assert row == (data["nickname"], data["language"], data["privacy"], data["playlist"], data["theme"])

        # reset to default settings
        async with client.post(
            "/account/change_settings",
            data={
                "csrf": await get_csrf(client),
                "nickname": "",
                "language": "",
                "privacy": "",
                "playlist": "",
                "theme": theme.DEFAULT_THEME,
            },
        ) as response:
            response.raise_for_status()

        with db.connect(read_only=True) as conn:
            row = conn.execute(
                "SELECT nickname, language, privacy, primary_playlist, theme FROM user WHERE username=?",
                (TEST_USERNAME,),
            ).fetchone()
            assert row == (None, None, None, None, theme.DEFAULT_THEME)


async def test_change_password(client: T_client):
    data = {
        "csrf": await get_csrf(client),
        "current_password": TEST_PASSWORD + "a",
        "new_password": TEST_PASSWORD,
    }
    # should fail when provided with invalid current password
    async with client.post("/account/change_password", data=data) as response:
        assert response.status == web.HTTPBadRequest.status_code
    # should succeed with valid password
    data["current_password"] = TEST_PASSWORD
    async with client.post("/account/change_password", data=data) as response:
        response.raise_for_status()
