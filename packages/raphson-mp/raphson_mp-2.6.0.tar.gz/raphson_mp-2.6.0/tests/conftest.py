from collections.abc import AsyncIterator

import pytest
from aiohttp.test_utils import TestClient, TestServer

from raphson_mp import db
from raphson_mp.common.music import Album, Artist, Playlist
from raphson_mp.server import Server

from . import TEST_PASSWORD, TEST_USERNAME, T_client


@pytest.fixture()
async def anonymous_client() -> AsyncIterator[T_client]:
    server = Server(False)
    test_server = TestServer(server.app)
    await test_server.start_server()
    client = TestClient(test_server)
    yield client
    await client.close()


@pytest.fixture()
async def client(anonymous_client: T_client) -> AsyncIterator[T_client]:
    async with anonymous_client.post(
        "/auth/login", data={"username": TEST_USERNAME, "password": TEST_PASSWORD}, allow_redirects=False
    ) as response:
        assert response.status == 303

    yield anonymous_client


# @pytest.fixture()
# async def playlist():
#     playlist_name = "test-" + random.randbytes(8).hex()
#     playlist_path = Path(settings.music_dir, playlist_name)
#     try:
#         playlist_path.mkdir()
#         await scanner.scan_playlists()
#         # give user write access to newly created playlist
#         with db.connect() as conn:
#             (user_id,) = conn.execute("SELECT id FROM user WHERE username=?", (TEST_USERNAME,)).fetchone()
#             conn.execute("INSERT INTO user_playlist_write VALUES (?, ?)", (user_id, playlist_name))
#         yield playlist_name
#     finally:
#         shutil.rmtree(playlist_path)
#         await scanner.scan_playlists()


# @pytest.fixture()
# async def track(playlist: str):
#     path = Path(settings.music_dir, playlist, random.randbytes(4).hex() + ".ogg")
#     async with aiohttp.ClientSession() as session:
#         async with session.get("https://downloads.rkslot.nl/cipher.ogg") as response:
#             assert response.status == 200
#             path.write_bytes(await response.read())
#     with db.connect(read_only=True) as conn:
#         await scanner.scan_playlist(None, music.Playlist.by_name(conn, playlist))
#     yield music.to_relpath(path)


@pytest.fixture()
def playlist():
    with db.connect() as conn:
        (playlist,) = conn.execute("SELECT name FROM playlist ORDER BY RANDOM() LIMIT 1").fetchone()

        # Give test user write access to this playlist
        conn.execute(
            "INSERT OR IGNORE INTO user_playlist_write VALUES ((SELECT id FROM user WHERE username=?), ?)",
            (TEST_USERNAME, playlist),
        )

    return Playlist(playlist)


@pytest.fixture()
def track():
    with db.connect(read_only=True) as conn:
        (path,) = conn.execute("SELECT path FROM track ORDER BY RANDOM() LIMIT 1").fetchone()
    return path


@pytest.fixture()
def artist():
    with db.connect(read_only=True) as conn:
        artist, track = conn.execute("SELECT artist, track FROM track_artist ORDER BY RANDOM() LIMIT 1").fetchone()
    return Artist(artist, track)


@pytest.fixture()
def album():
    with db.connect(read_only=True) as conn:
        album, artist, track = conn.execute(
            "SELECT album, album_artist, path FROM track ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
    return Album(album, artist, track)
