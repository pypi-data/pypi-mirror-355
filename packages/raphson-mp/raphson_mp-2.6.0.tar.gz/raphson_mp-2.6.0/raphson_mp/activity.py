import asyncio
import logging
import time
from collections.abc import Iterator
from dataclasses import dataclass
from sqlite3 import Connection
from typing import cast

from raphson_mp import db, event, lastfm
from raphson_mp.auth import PrivacyOption, StandardUser, User
from raphson_mp.common.control import ServerPlaying
from raphson_mp.music import Track

_LOGGER = logging.getLogger(__name__)


@dataclass
class NowPlaying:
    player_id: str
    user_id: int
    username: str
    update_time: int
    lastfm_update_timestamp: int
    paused: bool
    position: float
    duration: float
    control: bool
    volume: float
    track: Track | None

    def control_command(self) -> ServerPlaying:
        return ServerPlaying(
            player_id=self.player_id,
            username=self.username,
            update_time=self.update_time,
            paused=self.paused,
            position=self.position,
            duration=self.duration,
            control=self.control,
            volume=self.volume,
            track=self.track.to_dict() if self.track else None,
        )


_NOW_PLAYING: dict[str, NowPlaying] = {}


def now_playing() -> Iterator[NowPlaying]:
    current_time = int(time.time())
    for entry in _NOW_PLAYING.values():
        if entry.update_time > current_time - 120:
            yield entry


async def set_now_playing(
    conn: Connection,
    user: User,
    player_id: str,
    relpath: str | None,
    paused: bool,
    position: float,
    duration: float,
    control: bool,
    volume: float,
) -> None:
    track = Track(conn, relpath) if relpath else None
    current_time = int(time.time())
    username = user.nickname if user.nickname else user.username

    now_playing = NowPlaying(
        player_id,
        user.user_id,
        username,
        current_time,
        current_time,
        paused,
        position,
        duration,
        control,
        volume,
        track,
    )
    _NOW_PLAYING[player_id] = now_playing

    if track and not paused and now_playing.lastfm_update_timestamp < current_time - 60:
        user_key = lastfm.get_user_key(cast(StandardUser, user))
        if user_key:
            await lastfm.update_now_playing(user_key, track)
            now_playing.lastfm_update_timestamp = current_time

    await event.fire(event.NowPlayingEvent(now_playing))


async def set_played(user: User, track: Track, timestamp: int):
    private = user.privacy == PrivacyOption.AGGREGATE

    if not private:
        await event.fire(event.TrackPlayedEvent(user, timestamp, track))

    def thread():
        with db.connect() as writable_conn:
            writable_conn.execute(
                """
                INSERT INTO history (timestamp, user, track, playlist, private)
                VALUES (?, ?, ?, ?, ?)
                """,
                (timestamp, user.user_id, track.path, track.playlist, private),
            )

    await asyncio.to_thread(thread)

    # last.fm requires track length to be at least 30 seconds
    if not private and track.duration >= 30:
        lastfm_key = lastfm.get_user_key(cast(StandardUser, user))
        if lastfm_key:
            await lastfm.scrobble(lastfm_key, track, timestamp)


async def stop_playing(user: User, player_id: str):
    playing = _NOW_PLAYING.get(player_id)
    if playing is None:
        return

    if playing.user_id != user.user_id:
        _LOGGER.warning("user %s attempted to stop player owned by different user %s", user.username, playing.user_id)
        return

    _LOGGER.debug("player %s stopped playing", player_id)
    del _NOW_PLAYING[player_id]
    await event.fire(event.StoppedPlayingEvent(player_id))
