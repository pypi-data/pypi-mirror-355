from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
from abc import ABC
from collections.abc import Awaitable, Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from aiohttp import ClientWebSocketResponse, web
from typing_extensions import override

from raphson_mp.common.track import TrackDict

_LOGGER = logging.getLogger(__name__)


class Topic(Enum):
    ACTIVITY = "activity"


@dataclass(kw_only=True)
class Command(ABC):
    name: str

    def data(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_data(cls, data: dict[str, str]) -> Command:
        assert data["name"] == cls.name
        return cls(**data)

    async def send(self, ws: web.WebSocketResponse | ClientWebSocketResponse) -> None:
        try:
            await ws.send_json(self.data())
        except ConnectionError:
            pass


@dataclass(kw_only=True)
class ServerCommand(Command, ABC):
    """Represents a command from the server"""


@dataclass(kw_only=True)
class ClientCommand(Command, ABC):
    """Represents a command from the client"""


@dataclass(kw_only=True)
class ClientPlaying(ClientCommand):
    """Sent from player client to server, to let the server know about its current state"""

    name: str = "c_playing"
    track: str | None
    paused: bool
    position: float
    duration: float
    control: bool = False  # TODO remove default value after all clients have been updated
    volume: float = 1.0  # TODO remove default value after all clients have been updated


@dataclass(kw_only=True)
class ClientSubscribe(ClientCommand):
    """Command to subscribe to topics (events) from a client"""

    name: str = "c_subscribe"
    topic: Topic

    @override
    def data(self) -> dict[str, Any]:
        return {"name": self.name, "topic": self.topic.value}

    @override
    @classmethod
    def from_data(cls, data: dict[str, str]) -> Command:
        return cls(topic=Topic(data["topic"]))


@dataclass(kw_only=True)
class ClientToken(ClientCommand):
    """When authenticated using cookies, sending a csrf token is required before sending any other commands"""

    name: str = "c_token"
    csrf: str


@dataclass(kw_only=True)
class PlayerControlCommand(ABC):
    """
    A command sent from a client to the server, relayed by the server to a second client (with player_id) to control it
    """

    player_id: str


@dataclass(kw_only=True)
class ClientPlay(ClientCommand, PlayerControlCommand):
    """Instruct a player to start playing"""

    name: str = "c_play"


@dataclass(kw_only=True)
class ClientPause(ClientCommand, PlayerControlCommand):
    """Instruct a player to pause"""

    name: str = "c_pause"


@dataclass(kw_only=True)
class ClientPrevious(ClientCommand, PlayerControlCommand):
    """Instruct a player to go to the previous track"""

    name: str = "c_previous"


@dataclass(kw_only=True)
class ClientNext(ClientCommand, PlayerControlCommand):
    """Instruct a player to go to the next track"""

    name: str = "c_next"


@dataclass(kw_only=True)
class ClientVolume(ClientCommand, PlayerControlCommand):
    """Instruct a player to change its volume"""

    name: str = "c_volume"
    volume: float


@dataclass(kw_only=True)
class ServerPlaying(ServerCommand):
    """
    ClientPlaying command relayed by the server as ServerPlaying command to clients subscribed to Topic.ACTIVITY
    """

    name: str = "s_playing"
    player_id: str
    username: str  # nickname or username
    update_time: float  # timestamp of last update, for current position extrapolation
    paused: bool  # whether media is paused
    position: float  # position in playing track
    duration: float  # duration of track
    control: bool  # whether control is supported
    volume: float  # current volume 0.0-1.0
    track: TrackDict | None


@dataclass(kw_only=True)
class ServerPlayed(ServerCommand):
    name: str = "s_played"
    played_time: int  # timestamp at which track was played
    username: str  # nickname or username
    track: TrackDict


@dataclass(kw_only=True)
class ServerPlayingStopped(ServerCommand):
    """Fired when a player has stopped playing"""

    name: str = "s_playing_stopped"
    player_id: str


class FileAction(Enum):
    INSERT = "insert"
    DELETE = "delete"
    UPDATE = "update"
    MOVE = "move"


@dataclass(kw_only=True)
class ServerFileChange(ServerCommand):
    name: str = "s_file_change"
    change_time: int
    action: FileAction
    track: str
    username: str | None

    @override
    def data(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "change_time": self.change_time,
            "action": self.action.value,
            "track": self.track,
            "username": self.username,
        }

    @override
    @classmethod
    def from_data(cls, data: dict[str, Any]) -> Command:
        return cls(
            change_time=data["change_time"],
            action=FileAction(data["action"]),
            track=data["track"],
            username=data["username"],
        )


@dataclass(kw_only=True)
class ServerPlay(ServerCommand):
    name: str = "s_play"


@dataclass(kw_only=True)
class ServerPause(ServerCommand):
    name: str = "s_pause"


@dataclass(kw_only=True)
class ServerPrevious(ServerCommand):
    name: str = "s_previous"


@dataclass(kw_only=True)
class ServerNext(ServerCommand):
    name: str = "s_next"


@dataclass(kw_only=True)
class ServerVolume(ServerCommand):
    name: str = "s_volume"
    volume: float


COMMMANDS: list[type[Command]] = [
    ClientPlaying,
    ClientSubscribe,
    ClientToken,
    ClientPlay,
    ClientPause,
    ClientPrevious,
    ClientNext,
    ServerPlaying,
    ServerPlayed,
    ServerFileChange,
    ServerPlay,
    ServerPause,
    ServerPrevious,
    ServerNext,
]

_BY_NAME: dict[str, type[Command]] = {}

for command in COMMMANDS:
    _BY_NAME[command.name] = command


def parse(message: str) -> Command:
    json_message = json.loads(message)
    command_t = _BY_NAME.get(json_message["name"])
    if command_t is None:
        raise ValueError("unknown command")
    command = command_t.from_data(json_message)
    return command


async def send(
    sockets: (
        ClientWebSocketResponse
        | web.WebSocketResponse
        | Iterable[web.WebSocketResponse]
        | Iterable[ClientWebSocketResponse]
    ),
    commands: Command | Iterable[Command],
):
    _LOGGER.debug("sending %s", commands)

    if isinstance(commands, Command):
        commands = [commands]

    if isinstance(sockets, ClientWebSocketResponse) or isinstance(sockets, web.WebSocketResponse):
        await asyncio.gather(*[command.send(sockets) for command in commands])
    else:
        awaitables: list[Awaitable[None]] = []
        for socket in sockets:
            awaitables.extend([command.send(socket) for command in commands])
        await asyncio.gather(*awaitables)
