import shutil
from pathlib import Path
from urllib.parse import quote

from aiohttp import web

from raphson_mp import music, settings
from raphson_mp.common.music import Playlist

from .conftest import T_client


async def test_unauthorized(anonymous_client: T_client):
    async with anonymous_client.get("/dav") as response:
        assert response.status == web.HTTPUnauthorized.status_code
        assert "WWW-Authenticate" in response.headers


async def test_options(client: T_client):
    async with client.options("/dav") as response:
        assert "DAV" in response.headers
    async with client.options("/dav") as response:
        assert "DAV" in response.headers


async def test_propfind(client: T_client):
    async with client.request("PROPFIND", "/dav", headers={"Depth": "0"}) as response:
        assert response.status == 207
        assert response.content_type == "application/xml"
        # xml = ET.fromstring(await response.text())
        # assert len(xml.findall("d:href", {"d": "DAV:"})) == 1

    async with client.request("PROPFIND", "/dav", headers={"Depth": "1"}) as response:
        pass
        # xml = ET.fromstring(await response.text())
        # assert len(xml.findall("d:href", {"d": "DAV:"})) > 1


async def test_get_put_delete(client: T_client, playlist: Playlist):
    test_data = Path("docs/tyrone_music.jpg").read_bytes()
    test_path = Path(settings.music_dir, "test_file")
    try:
        test_path.write_bytes(test_data)
        shutil.copy(Path("docs/tyrone_music.jpg"), test_path)
        relpath = music.to_relpath(test_path)
        async with client.get("/dav/" + quote(relpath)) as response:
            assert test_data == await response.read()
    finally:
        test_path.unlink()

    async with client.get("/dav/404notfound") as response:
        assert response.status == web.HTTPNotFound.status_code

    async with client.put("/dav/new_file", data=test_data) as response:
        assert response.status == web.HTTPForbidden.status_code

    async with client.put("/dav/" + playlist.name + "/new_file", data=test_data) as response:
        assert response.status == web.HTTPCreated.status_code

    new_file = Path(settings.music_dir, playlist.name, "new_file")
    assert new_file.is_file()

    async with client.delete("/dav/" + playlist.name) as response:
        assert response.status == web.HTTPForbidden.status_code

    async with client.delete("/dav/" + playlist.name + "/new_file") as response:
        assert response.status == web.HTTPNoContent.status_code

    async with client.delete("/dav/" + playlist.name + "/new_file") as response:
        assert response.status == web.HTTPMethodNotAllowed.status_code


# def _scanner_log():
#     with db.connect() as conn:
#         return conn.execute("SELECT action, track FROM scanner_log ORDER BY timestamp DESC LIMIT 1").fetchone()


# async def test_move_mkcol(client: T_client, playlist: str, track: str):
#     assert playlist == music.relpath_playlist(track)

#     async with client.request("MKCOL", "/dav/" + playlist + "/mapje") as response:
#         assert response.status == web.HTTPCreated.status_code
#     async with client.request("MKCOL", "/dav/" + playlist + "/mapje") as response:
#         assert response.status == web.HTTPConflict.status_code

#     new_relpath = playlist + "/mapje/" + track.split("/")[-1]
#     async with client.request(
#         "MOVE", "/dav/" + quote(track), headers={"Destination": "/dav/" + new_relpath}
#     ) as response:
#         assert response.status == web.HTTPNoContent.status_code, await response.text()
#         assert _scanner_log() == ("move", new_relpath)

#     # move directory
#     async with client.request(
#         "MOVE", "/dav/" + playlist + "/mapje", headers={"Destination": "/dav/" + playlist + "/mapje2"}
#     ):
#         assert response.status == web.HTTPNoContent.status_code, await response.text()
#         assert _scanner_log() == ("move", playlist + "/mapje2/" + track.split("/")[-1])
