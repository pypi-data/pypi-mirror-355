import hmac
import logging
import time
from sqlite3 import Connection
from weakref import WeakSet, WeakValueDictionary

from aiohttp import WSMsgType, web

from raphson_mp import activity, event
from raphson_mp.auth import User
from raphson_mp.common.control import (
    ClientNext,
    ClientPause,
    ClientPlay,
    ClientPlaying,
    ClientPrevious,
    ClientSubscribe,
    ClientToken,
    ClientVolume,
    PlayerControlCommand,
    ServerCommand,
    ServerFileChange,
    ServerNext,
    ServerPause,
    ServerPlay,
    ServerPlayed,
    ServerPlayingStopped,
    ServerPrevious,
    ServerVolume,
    Topic,
    parse,
    send,
)
from raphson_mp.decorators import route
from raphson_mp.vars import CLOSE_RESPONSES

_LOGGER = logging.getLogger(__name__)

_BY_ID: WeakValueDictionary[str, web.WebSocketResponse] = WeakValueDictionary()
_SUB_ACTIVITY: WeakSet[web.WebSocketResponse] = WeakSet()

SIMPLE_PLAYER_CONTROL_COMMANDS: dict[type[PlayerControlCommand], ServerCommand] = {
    ClientPlay: ServerPlay(),
    ClientPause: ServerPause(),
    ClientPrevious: ServerPrevious(),
    ClientNext: ServerNext(),
}

received_message_counter: int = 0


@route("", method="GET")
async def websocket(request: web.Request, conn: Connection, user: User):
    control_id = request.query.get("id")

    if control_id is None:
        raise web.HTTPBadRequest(reason="missing id")

    # If cookies are set, they may have been used to log in and CSRF is possible. In this case,
    # the client must first provide CSRF token before it is trusted.
    trusted = "Cookie" not in request.headers

    ws = web.WebSocketResponse()

    _BY_ID[control_id] = ws
    request.config_dict[CLOSE_RESPONSES].add(ws)

    await ws.prepare(request)

    async for message in ws:
        if message.type == WSMsgType.TEXT:
            try:
                command = parse(message.data)
                _LOGGER.info("received message %s", command)
            except Exception:
                _LOGGER.warning("failed to parse message %s", message.data, exc_info=True)
                continue

            global received_message_counter
            received_message_counter += 1

            if not trusted:
                if isinstance(command, ClientToken):
                    if hmac.compare_digest(user.csrf, command.csrf):
                        trusted = True
                    else:
                        _LOGGER.warning("invalid CSRF token")
                else:
                    _LOGGER.info("ignoring command, client needs to send CSRF token first")
                continue

            if isinstance(command, ClientPlaying):
                await activity.set_now_playing(
                    conn,
                    user,
                    control_id,
                    command.track,
                    command.paused,
                    command.position,
                    command.duration,
                    command.control,
                    command.volume,
                )
            elif isinstance(command, ClientSubscribe):
                if command.topic == Topic.ACTIVITY:
                    _SUB_ACTIVITY.add(ws)

                    # send current data to the client immediately
                    commands = [playing.control_command() for playing in activity.now_playing()]

                    await send(ws, commands)
            elif isinstance(command, PlayerControlCommand):
                target = _BY_ID.get(command.player_id)
                if target is not None:
                    if isinstance(command, ClientVolume):
                        await send(target, ServerVolume(volume=command.volume))
                    else:
                        command_to_send = SIMPLE_PLAYER_CONTROL_COMMANDS[type(command)]
                        await send(target, command_to_send)
                else:
                    _LOGGER.warning("unknown player id")
            else:
                _LOGGER.warning("ignoring unsupported command: %s", command)

    return ws


async def broadcast_playing(event: event.NowPlayingEvent) -> None:
    await send(_SUB_ACTIVITY, event.now_playing.control_command())


async def broadcast_stop_playing(event: event.StoppedPlayingEvent) -> None:
    await send(_SUB_ACTIVITY, ServerPlayingStopped(player_id=event.player_id))


async def broadcast_history(event: event.TrackPlayedEvent):
    await send(
        _SUB_ACTIVITY,
        ServerPlayed(
            username=event.user.nickname if event.user.nickname else event.user.username,
            played_time=event.timestamp,
            track=event.track.to_dict(),
        ),
    )


async def broadcast_file_change(event: event.FileChangeEvent):
    username = None
    if event.user:
        username = event.user.nickname if event.user.nickname else event.user.username
    await send(
        _SUB_ACTIVITY,
        ServerFileChange(change_time=int(time.time()), action=event.action, track=event.track, username=username),
    )


event.subscribe(event.NowPlayingEvent, broadcast_playing)
event.subscribe(event.StoppedPlayingEvent, broadcast_stop_playing)
event.subscribe(event.TrackPlayedEvent, broadcast_history)
event.subscribe(event.FileChangeEvent, broadcast_file_change)
