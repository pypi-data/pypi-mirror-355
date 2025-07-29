import logging
import time
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass

import aiohttp

from raphson_mp import cache, httpclient, settings
from raphson_mp.util import urlencode

log = logging.getLogger(__name__)


@dataclass
class SpotifyTrack:
    title: str
    artists: list[str]

    @property
    def display(self) -> str:
        return ", ".join(self.artists) + " - " + self.title


class SpotifyClient:

    _access_token: str | None = None
    _access_token_expiry: int = 0

    async def get_access_token(self) -> str:
        if self._access_token is not None:
            if self._access_token_expiry > int(time.time()):
                return self._access_token

        assert settings.spotify_api_id
        assert settings.spotify_api_secret

        async with httpclient.session() as session:
            async with session.post(
                "https://accounts.spotify.com/api/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.spotify_api_id,
                    "client_secret": settings.spotify_api_secret,
                },
            ) as response:
                json = await response.json()

        access_token: str = json["access_token"]
        self._access_token = access_token
        self._access_token_expiry = int(time.time()) + json["expires_in"]
        return access_token

    async def _session(self) -> AbstractAsyncContextManager[aiohttp.ClientSession]:
        return httpclient.session(
            headers={
                "Authorization": "Bearer " + await self.get_access_token(),
            },
        )

    async def get_playlist(self, playlist_id: str) -> AsyncIterator[SpotifyTrack]:
        url = "https://api.spotify.com/v1/playlists/" + urlencode(playlist_id) + "/tracks"

        async with await self._session() as session:
            while url:
                log.info("making request to: %s", url)

                async with session.get(url, params={"fields": "next,items(track(name,artists(name)))"}) as response:
                    json = await response.json()

                for track in json["items"]:
                    title = track["track"]["name"]
                    artists = [artist["name"] for artist in track["track"]["artists"]]
                    yield SpotifyTrack(title, artists)

                url = json["next"]

    async def _get_artist_image(self, name: str):
        async with await self._session() as session:
            async with session.get(
                "https://api.spotify.com/v1/search",
                params={"q": "artist:" + name, "type": "artist", "market": "NL", "limit": 1},
            ) as response:
                json = await response.json()
                items = json["artists"]["items"]
                if not items:
                    return cache.CacheData(b"no_cover", cache.MONTH)
                artist = items[0]
                images = artist["images"]
                if not images:
                    return cache.CacheData(b"no_cover", cache.MONTH)
                image_url = images[0]['url']

        log.debug('downloading image: %s', image_url)

        async with httpclient.session() as session:
            async with session.get(image_url) as response:
                image_bytes = await response.content.read()

        return cache.CacheData(image_bytes, cache.HALFYEAR)

    async def get_artist_image(self, name: str) -> bytes | None:
        image_bytes = await cache.retrieve_or_store("spotify_artist_image" + name, self._get_artist_image, name)
        if image_bytes == b"no_cover":
            return None
        return image_bytes


_cached_client: SpotifyClient | None = None
def client() -> SpotifyClient:
    global _cached_client
    if _cached_client:
        return _cached_client
    return (_cached_client := SpotifyClient())
