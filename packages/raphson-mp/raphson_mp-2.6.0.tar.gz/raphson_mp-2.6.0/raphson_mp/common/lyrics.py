# pyright: reportTypedDictNotRequiredAccess=false
import json
import re
from abc import ABC
from dataclasses import dataclass
from typing import NotRequired, TypedDict, cast


class Lyrics(ABC):
    source: str


@dataclass
class LyricsLine:
    start_time: float
    text: str


@dataclass
class TimeSyncedLyrics(Lyrics):
    source: str
    text: list[LyricsLine]

    def to_plain(self) -> "PlainLyrics":
        text = "\n".join([line.text for line in self.text])
        return PlainLyrics(self.source, text)

    def to_lrc(self) -> str:
        lrc = ""
        for line in self.text:
            minutes, seconds = divmod(line.start_time, 60)
            lrc += f"[{int(minutes):02d}:{seconds:05.2f}] {line.text}\n"
        return lrc

    @classmethod
    def from_lrc(cls, source: str, lrc: str):
        lines: list[LyricsLine] = []
        for line in lrc.splitlines():
            matches = re.findall(r"\[(\d{2}):(\d{2})\.(\d{2})\](?: (.*))?", line)
            if matches:
                minutes, seconds, centiseconds, text = matches[0]
                lines.append(LyricsLine(int(minutes) * 60 + int(seconds) + int(centiseconds) / 100, text))
        return cls(source, lines)


@dataclass
class PlainLyrics(Lyrics):
    source: str
    text: str


def from_text(source: str, text: str | None) -> Lyrics | None:
    if text is None:
        return None
    synced = TimeSyncedLyrics.from_lrc(source, text)
    # TimeSyncedLyrics matcher skips lines that don't match the regex
    # if the line count is significantly lower than expected, the text is probably not in LRC format
    if len(synced.text) * 2 > text.count("\n"):
        return synced
    return PlainLyrics(source, text)


def ensure_plain(lyr: Lyrics | None) -> PlainLyrics | None:
    if lyr is None:
        return None
    elif isinstance(lyr, TimeSyncedLyrics):
        return lyr.to_plain()
    elif isinstance(lyr, PlainLyrics):
        return lyr
    else:
        raise ValueError(lyr)


class LyricsLineDict(TypedDict):
    start_time: float
    text: str


class LyricsDict(TypedDict):
    type: str
    source: NotRequired[str]
    text: NotRequired[str | list[LyricsLineDict]]


def to_dict(lyrics: Lyrics | None) -> LyricsDict:
    if lyrics is None:
        return {"type": "none"}
    elif isinstance(lyrics, TimeSyncedLyrics):
        text: list[LyricsLineDict] = [{"start_time": line.start_time, "text": line.text} for line in lyrics.text]
        return {"type": "synced", "source": lyrics.source, "text": text}
    elif isinstance(lyrics, PlainLyrics):
        return {"type": "plain", "source": lyrics.source, "text": lyrics.text}
    else:
        raise ValueError(lyrics)


def from_dict(dict: LyricsDict) -> Lyrics | None:
    if dict["type"] == "none":
        return None

    if dict["type"] == "synced":
        lines = [LyricsLine(line["start_time"], line["text"]) for line in cast(list[LyricsLineDict], dict["text"])]
        return TimeSyncedLyrics(dict["source"], text=lines)

    if dict["type"] == "plain":
        return PlainLyrics(dict["source"], cast(str, dict["text"]))

    raise ValueError(dict["type"])


def to_bytes(lyrics: Lyrics | None):
    return json.dumps(to_dict(lyrics)).encode()


def from_bytes(data: bytes) -> Lyrics | None:
    return from_dict(json.loads(data))
