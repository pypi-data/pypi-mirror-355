# pyright: reportUnreachable=false
import asyncio
import random
import time
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from aiohttp.test_utils import TestServer

from raphson_mp import db, settings
from raphson_mp.client import RaphsonMusicClient
from raphson_mp.client.track import Track
from raphson_mp.common.control import (
    ClientPlaying,
    ClientSubscribe,
    ServerCommand,
    ServerPlaying,
    Topic,
)
from raphson_mp.common.image import ImageFormat, ImageQuality
from raphson_mp.common.playlist import Playlist
from raphson_mp.common.track import AudioFormat
from raphson_mp.server import Server


def setup_module():
    settings.data_dir = Path("./data").resolve()
    settings.music_dir = Path("./music").resolve()


@pytest.fixture
async def client() -> AsyncIterator[RaphsonMusicClient]:
    with db.connect(read_only=True) as conn:
        (token,) = conn.execute("SELECT token FROM session LIMIT 1").fetchone()

    print("obtained arbitrary token from database:", token)

    server = Server(False)
    test_server = TestServer(server.app)
    await test_server.start_server()
    client = RaphsonMusicClient()
    base_url = str(test_server._root)
    await client.setup(base_url=base_url, token=token, user_agent="client test suite")
    yield client
    await client.close()
    await test_server.close()


async def get_random_playlist(client: RaphsonMusicClient, ignore_empty: bool = False) -> Playlist:
    playlists = await client.playlists()
    if ignore_empty:
        playlists = [playlist for playlist in playlists if playlist.track_count > 0]
    playlist = random.choice(playlists)
    assert isinstance(playlist.name, str), playlist
    assert isinstance(playlist.track_count, int), playlist
    assert isinstance(playlist.favorite, bool), playlist
    assert isinstance(playlist.write, bool), playlist
    return playlist


async def get_random_track(client: RaphsonMusicClient) -> Track:
    playlist = await get_random_playlist(client, ignore_empty=True)
    track = await client.choose_track(playlist)
    assert isinstance(track.playlist, str)
    assert isinstance(track.path, str)
    assert isinstance(track.mtime, int)
    assert isinstance(track.duration, int)
    assert isinstance(track.title, str | None)
    assert isinstance(track.album, str | None)
    assert isinstance(track.album_artist, str | None)
    assert isinstance(track.year, int | None)
    assert isinstance(track.artists, list)
    assert isinstance(track.tags, list)
    assert isinstance(track.video, str | None)
    assert isinstance(track.lyrics, str | None)
    return track


async def test_choose_track(client: RaphsonMusicClient):
    track = await get_random_track(client)
    track2 = await client.get_track(track.path)
    assert track == track2


async def test_download_news(client: RaphsonMusicClient):
    await client.get_news()


async def test_list_tracks(client: RaphsonMusicClient):
    playlist = await get_random_playlist(client, ignore_empty=True)
    tracks = await client.list_tracks(playlist.name)
    track = random.choice(tracks)
    await client.get_track(track.path)  # verify the track exists


async def test_download_cover(client: RaphsonMusicClient):
    track = await get_random_track(client)
    await asyncio.gather(
        *[
            track.get_cover_image(format=format, quality=quality, meme=meme)
            for format in ImageFormat
            for quality in ImageQuality
            for meme in (False, True)
        ]
    )


async def test_now_playing(client: RaphsonMusicClient):
    track: Track | None = None
    received_events: int = 0

    async def handler(command: ServerCommand):
        if not isinstance(command, ServerPlaying):
            return

        nonlocal received_events
        received_events += 1

        assert abs(command.update_time - time.time()) < 1

        if track is None:
            assert command.track == None
        else:
            assert command.track["path"] == track.path
            assert command.position > 0
            assert command.duration == track.duration
            assert command.paused == True

    client.control_start(handler=handler)

    # Before subscription (should be received as soon as subscription is started)
    await client.control_send(ClientPlaying(track=None, paused=False, position=31.5, duration=70))

    # Subscribe now
    await client.control_send(ClientSubscribe(topic=Topic.ACTIVITY))

    # Wait for websocket receive
    async with asyncio.timeout(5):
        while received_events != 1:  # pyright: ignore[reportUnnecessaryComparison]
            await asyncio.sleep(0)

    # Now playing with track info
    track = await get_random_track(client)
    await client.control_send(
        ClientPlaying(track=track.path, paused=True, position=track.duration / 2, duration=track.duration)
    )

    # Wait for websocket receive
    async with asyncio.timeout(5):
        while received_events != 2:
            await asyncio.sleep(0)

    # Now playing without track info
    track = None
    await client.control_send(ClientPlaying(track=None, paused=False, position=31.5, duration=70))

    # Wait for websocket receive
    async with asyncio.timeout(5):
        while received_events != 3:
            await asyncio.sleep(0)

    await client.control_stop()

    assert received_events == 3


async def test_share(client: RaphsonMusicClient):
    track = await get_random_track(client)
    share = await track.share()
    tracks = await share.tracks()
    assert len(tracks) == 1
    for track in tracks:
        assert await track.audio()
        assert await track.cover()


# this test is at the end because it takes a while
async def test_download_audio(client: RaphsonMusicClient):
    track = await get_random_track(client)
    await asyncio.gather(*[track.get_audio(format) for format in AudioFormat])
