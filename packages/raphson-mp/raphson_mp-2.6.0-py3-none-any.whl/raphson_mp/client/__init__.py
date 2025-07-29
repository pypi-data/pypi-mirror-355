import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from io import UnsupportedOperation

from aiohttp import (
    ClientError,
    ClientResponseError,
    ClientTimeout,
    ClientWebSocketResponse,
    StreamReader,
    WSMsgType,
)
from aiohttp.client import ClientSession

from raphson_mp.client.track import DownloadedTrack, Track
from raphson_mp.common.control import ClientCommand, ServerCommand, parse
from raphson_mp.common.playlist import Playlist
from raphson_mp.util import urlencode

_LOGGER = logging.getLogger(__name__)


class RaphsonMusicClient:
    player_id: str
    session: ClientSession
    cached_rapson_logo: bytes | None = None
    control_task: asyncio.Task[None] | None = None
    control_ws: ClientWebSocketResponse | None = None

    def __init__(self):
        self.player_id = str(uuid.uuid4())
        self.session = None  # pyright: ignore[reportAttributeAccessIssue]

    async def setup(self, *, base_url: str, user_agent: str, token: str) -> None:
        self.session = ClientSession(
            base_url=base_url,
            headers={"User-Agent": user_agent, "Authorization": "Bearer " + token},
            timeout=ClientTimeout(connect=5, total=60),
            raise_for_status=True,
        )

    async def close(self) -> None:
        if self.session:
            await self.session.close()

    async def choose_track(self, playlist: Playlist | str) -> Track:
        if isinstance(playlist, Playlist):
            playlist = playlist.name
        async with self.session.post("/playlist/" + urlencode(playlist) + "/choose_track", json={}) as response:
            json = await response.json()
        return Track(json, self.session)

    async def get_track(self, path: str) -> Track:
        async with self.session.get("/track/" + urlencode(path) + "/info") as response:
            json = await response.json()
        return Track(json, self.session)

    async def submit_played(self, track_path: str, timestamp: int) -> None:
        async with self.session.post("/activity/played", json={"track": track_path, "timestamp": timestamp}):
            pass

    async def _get_news_audio(self) -> bytes:
        async with self.session.get("/news/audio") as response:
            return await response.content.read()

    async def get_news(self) -> DownloadedTrack | None:
        try:
            audio, image = await asyncio.gather(self._get_news_audio(), self.get_raphson_logo())
            return DownloadedTrack(None, audio, image, '{"type":"none"}')
        except ClientResponseError as ex:
            if ex.status == 503:
                return None
            raise ex

    async def get_raphson_logo(self) -> bytes:
        if not self.cached_rapson_logo:
            async with self.session.get("/static/img/raphson.png") as response:
                self.cached_rapson_logo = await response.content.read()
        return self.cached_rapson_logo

    async def list_tracks_response(self, playlist: str) -> StreamReader:
        response = await self.session.get("/tracks/filter", params={"playlist": playlist})
        return response.content

    async def list_tracks(self, playlist: str) -> list[Track]:
        async with self.session.get("/tracks/filter", params={"playlist": playlist}) as response:
            response_json = await response.json()
        return [Track(track_json, self.session) for track_json in response_json["tracks"]]

    async def playlists(self) -> list[Playlist]:
        async with self.session.get("/playlist/list") as response:
            return [
                Playlist(playlist["name"], playlist["track_count"], playlist["favorite"], playlist["write"])
                for playlist in await response.json()
            ]

    async def dislikes(self) -> set[str]:
        async with self.session.get("/dislikes/json") as response:
            json = await response.json()
        return set(json["tracks"])

    async def _control_task(self, handler: Callable[[ServerCommand], Awaitable[ClientCommand | None]] | None = None):
        while True:
            try:
                async with self.session.ws_connect("/control", params={"id": self.player_id}) as ws:
                    self.control_ws = ws
                    async for message in ws:
                        if message.type == WSMsgType.TEXT:
                            if handler is None:
                                continue
                            command = parse(message.data)
                            assert isinstance(command, ServerCommand)
                            response = await handler(command)
                            if response:
                                await ws.send_json(response.data())
                        elif message.type == WSMsgType.ERROR:
                            break
            except ClientError:
                _LOGGER.warning("websocket connection failure, will reconnect in 10 seconds")
                await asyncio.sleep(10)
            finally:
                self.control_ws = None

    def control_start(self, handler: Callable[[ServerCommand], Awaitable[ClientCommand | None]] | None = None):
        if self.control_task and not self.control_task.done():
            raise UnsupportedOperation("control channel is already active")

        self.control_task = asyncio.create_task(self._control_task(handler))

    async def control_stop(self):
        if self.control_task and not self.control_task.done():
            self.control_task.cancel()

            try:
                await self.control_task
            except asyncio.CancelledError:
                pass

        self.control_task = None

    async def control_send(self, command: ClientCommand):
        retries = 0
        while not self.control_ws and retries < 1000:
            retries += 1
            await asyncio.sleep(1)

        if not self.control_ws:
            raise UnsupportedOperation("websocket is still not active after waiting 1 second")

        await command.send(self.control_ws)
