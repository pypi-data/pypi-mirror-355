import random
import secrets
from typing import cast

from raphson_mp import auth, db, theme

from . import TEST_PASSWORD, TEST_USERNAME, T_client, get_csrf

# --------------- LOGIN --------------- #


async def test_failed_login(client: T_client):
    async with client.post(
        "/auth/login", json={"username": TEST_USERNAME, "password": TEST_PASSWORD + "a"}, allow_redirects=False
    ) as response:
        assert response.status == 403


# --------------- ACCOUNT --------------- #


# def _db_nickname() -> None:
#     with db.connect(read_only=True) as conn:
#         return conn.execute("SELECT nickname FROM user WHERE username=?", (TEST_USERNAME,)).fetchone()[0]


# def test_change_nickname(self):
#     response = self.client.post('/account/change_nickname', data={'nickname': '🐢', 'csrf': self.csrf})
#     assert response.status_code == 303, (response.status_code, response.text)
#     assert self._db_nickname() == '🐢'


def _db_password_hash() -> str:
    with db.connect(read_only=True) as conn:
        return conn.execute("SELECT password FROM user WHERE username=?", (TEST_USERNAME,)).fetchone()[0]


async def test_change_password(client: T_client):
    initial_hash = _db_password_hash()
    csrf = await get_csrf(client)

    # wrong current_password
    async with client.post(
        "/account/change_password",
        data={
            "current_password": TEST_PASSWORD + "a",
            "new_password": "new_password",
            "repeat_new_password": "new_password",
            "csrf": csrf,
        },
    ) as response:
        assert response.status == 400, await response.text()
        assert _db_password_hash() == initial_hash  # password should not have changed

    # correct
    async with client.post(
        "/account/change_password",
        data={
            "current_password": TEST_PASSWORD,
            "new_password": "new_password",
            "repeat_new_password": "new_password",
            "csrf": csrf,
        },
        allow_redirects=False,
    ) as response:
        assert response.status == 303, await response.text()
        assert _db_password_hash() != initial_hash  # password should not have changed

    # restore initial password hash
    with db.connect() as conn:
        conn.execute(
            "UPDATE user SET password = ? WHERE username = ?",
            (
                initial_hash,
                TEST_USERNAME,
            ),
        )


# --------------- AUTH --------------- #


async def test_login_fail(client: T_client):
    async with client.post(
        "/auth/login", json={"username": TEST_USERNAME, "password": secrets.token_urlsafe(random.randint(1, 100))}
    ) as response:
        assert response.status == 403, await response.text()


async def test_login_json(client: T_client):
    async with client.post("/auth/login", json={"username": TEST_USERNAME, "password": TEST_PASSWORD}) as response:
        assert response.status == 200
        token = cast(str, (await response.json())["token"])
        assert len(token) > 10


async def test_user():
    with db.connect(read_only=True) as conn:
        (user_id,) = conn.execute("SELECT id FROM user WHERE username=?", (TEST_USERNAME,)).fetchone()
        user = auth.User.get(conn, user_id=user_id)
        assert isinstance(user, auth.StandardUser)
        assert user.conn is conn
        assert user.user_id == user_id
        assert user.username == TEST_USERNAME
        assert user.nickname is None
        assert user.admin == False
        assert user.primary_playlist is None
        assert user.language is None
        assert user.privacy is auth.PrivacyOption.NONE
        assert user.theme == theme.DEFAULT_THEME
