import hashlib
import secrets
from typing import cast
from raphson_mp import db
from raphson_mp.common.music import Album, Artist, Playlist
from raphson_mp.routes.subsonic import from_id, to_id
from tests import T_client


async def test_auth(client: T_client):
    with db.connect(read_only=True) as conn:
        token, username = conn.execute(
            "SELECT token, username FROM session JOIN user ON session.user = user.id LIMIT 1"
        ).fetchone()

    # No authentication
    async with client.get("/rest/ping") as response:
        response.raise_for_status()
        assert '<error code="42" />' in await response.text()

    # API key authentication
    async with client.get("/rest/ping", params={"apiKey": token}) as response:
        response.raise_for_status()
        assert 'status="ok"' in await response.text()
    async with client.get("/rest/ping", params={"apiKey": secrets.token_hex()}) as response:
        response.raise_for_status()
        assert '<error code="44" />' in await response.text()

    # Legacy authentication
    async with client.get("/rest/ping", params={"u": username, "p": token}) as response:
        response.raise_for_status()
        assert 'status="ok"' in await response.text()
    async with client.get("/rest/ping", params={"u": username, "p": token + "a"}) as response:
        response.raise_for_status()
        assert '<error code="40" />' in await response.text()

    # Hashed token authentication
    salt = secrets.token_hex()
    hash = hashlib.md5((token + salt).encode()).hexdigest()
    async with client.get("/rest/ping", params={"u": username, "t": hash, "s": salt}) as response:
        response.raise_for_status()
        assert 'status="ok"' in await response.text()
    async with client.get("/rest/ping", params={"u": username, "t": hash, "s": salt + "a"}) as response:
        response.raise_for_status()
        assert '<error code="40" />' in await response.text()


async def _request(client: T_client, endpoint: str, params: dict[str, str]):
    with db.connect(read_only=True) as conn:
        (token,) = conn.execute("SELECT token FROM session LIMIT 1").fetchone()

    # API key authentication
    async with client.get("/rest/" + endpoint, params={"apiKey": token, "f": "json", **params}) as response:
        response.raise_for_status()
        return (await response.json())["subsonic-response"]


async def test_id(artist: Artist, album: Album):
    track = "track/path"
    playlist = Playlist("Playlist")
    assert from_id(to_id(track)) == track
    assert from_id(to_id(artist)) == artist
    assert from_id(to_id(album)) == album
    assert from_id(to_id(playlist)) == playlist


async def test_getArtists(client: T_client):
    await _request(client, "getArtists", {})


async def test_getArtist(client: T_client, artist: Artist):
    artist_id = to_id(artist)
    response = await _request(client, "getArtist", {"id": artist_id})
    assert cast(Artist, from_id(response["artist"]["id"])).name == artist.name
    assert response["artist"]["name"] == artist.name
    assert response["artist"]["coverArt"] == response["artist"]["id"]


async def test_getAlbumList2(client: T_client):
    await _request(client, "getAlbumList2", {"type": "random"})
    await _request(client, "getAlbumList2", {"type": "newest"})
    await _request(client, "getAlbumList2", {"type": "highest"})
    await _request(client, "getAlbumList2", {"type": "frequent"})
    await _request(client, "getAlbumList2", {"type": "recent"})
    await _request(client, "getAlbumList2", {"type": "byYear", "fromYear": "2000", "toYear": "2010"})
    await _request(client, "getAlbumList2", {"type": "byGenre", "genre": "Pop"})
    await _request(client, "getAlbumList2", {"type": "alphabeticalByName"})
    await _request(client, "getAlbumList2", {"type": "alphabeticalByArtist"})


# TODO getCoverArt


async def test_getAlbum(client: T_client, album: Album):
    album_id = to_id(album)
    response = await _request(client, "getAlbum", {"id": album_id})
    assert cast(Album, from_id(response["album"]["id"])).name == album.name
    assert cast(Album, from_id(response["album"]["id"])).artist == album.artist
    assert response["album"]["name"] == album.name
    assert response["album"]["coverArt"] == response["album"]["id"]
    assert response["album"]["songCount"] >= 1
    assert response["album"]["duration"] > 10
    assert response["album"]["sortName"]
    assert isinstance(response["album"]["isCompilation"], bool)
