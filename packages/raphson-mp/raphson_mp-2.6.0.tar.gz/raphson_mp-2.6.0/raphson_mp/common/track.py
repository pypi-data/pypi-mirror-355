from datetime import datetime, timezone
from enum import Enum
import re
from typing import NotRequired, TypedDict

from attr import dataclass

from raphson_mp.common import metadata


# Also update TrackJson in static/js/types.d.ts
# TODO Clients have been updated on 2025-06-12 to support values being missing instead of null
# A few months after this date, the server can be updated to leave out values instead of sending null values
# This somewhat reduces the response size of track lists.
class TrackDict(TypedDict):
    path: str
    mtime: int
    ctime: int
    duration: int
    title: str | None
    album: str | None
    album_artist: str | None
    year: int | None
    track_number: int | None
    artists: list[str]
    tags: list[str]
    video: str | None
    lyrics: str | None

    # For compatibility with legacy clients. Returned by the server in responses, but not parsed by the client.
    playlist: NotRequired[str]
    display: NotRequired[str]


@dataclass(kw_only=True)
class TrackBase:
    path: str
    mtime: int
    ctime: int
    duration: int
    title: str | None
    album: str | None
    album_artist: str | None
    year: int | None
    track_number: int | None
    video: str | None
    lyrics: str | None
    artists: list[str]
    tags: list[str]

    def to_dict(self) -> TrackDict:
        return {
            "path": self.path,
            "mtime": self.mtime,
            "ctime": self.ctime,
            "duration": self.duration,
            "title": self.title,
            "album": self.album,
            "album_artist": self.album_artist,
            "year": self.year,
            "track_number": self.track_number,
            "artists": self.artists,
            "tags": self.tags,
            "video": self.video,
            "lyrics": self.lyrics,
            "playlist": self.playlist,
            "display": self.display_title()
        }

    @property
    def playlist(self) -> str:
        return self.path[: self.path.index("/")]

    @property
    def filename(self) -> str:
        return self.path[self.path.rindex("/") + 1:]

    @property
    def mtime_dt(self) -> datetime:
        return datetime.fromtimestamp(self.mtime, timezone.utc)

    @property
    def ctime_dt(self) -> datetime:
        return datetime.fromtimestamp(self.ctime, timezone.utc)

    def _filename_title(self) -> str:
        """
        Generate title from file name
        Returns: Title string
        """
        title = self.filename
        # Remove file extension
        try:
            title = title[: title.rindex(".")]
        except ValueError:
            pass
        # Remove YouTube id suffix
        title = re.sub(r" \[[a-zA-Z0-9\-_]+\]", "", title)
        title = metadata.strip_keywords(title)
        title = title.strip()
        return title

    def display_title(self, show_album: bool = True, show_year: bool = True) -> str:
        """
        Generate display title. It is generated using metadata if
        present, otherwise using the file name.
        """
        if self.title and self.artists:
            display = ", ".join(self.artists) + " - " + self.title

            if self.album and show_album:
                display += f" ({self.album}"
                if self.year and show_year:
                    display += f", {self.year})"
                else:
                    display += ")"
            elif self.year and show_year:
                display += f" ({self.year})"
            return display

        return self._filename_title()

    def download_name(self) -> str:
        """Name for a downloaded file. display_title() with some characters removed."""
        return re.sub(r"[^\x00-\x7f]", r"", self.display_title())

    @property
    def primary_artist(self) -> str | None:
        if self.artists:
            # if the album artist is also a track artist, the album artist is probably the primary artist
            if self.album_artist:
                if self.album_artist in self.artists:
                    return self.album_artist

            # if album artist is not known, we have to guess
            return self.artists[0]

        # no artists
        return None


class AudioFormat(Enum):
    """
    Opus audio in WebM container, for music player streaming.
    """

    WEBM_OPUS_HIGH = "webm_opus_high"

    """
    Opus audio in WebM container, for music player streaming with lower data
    usage.
    """
    WEBM_OPUS_LOW = "webm_opus_low"

    """
    MP3 files with metadata (including cover art), for use with external
    music player applications and devices Uses the MP3 format for broadest
    compatibility.
    """
    MP3_WITH_METADATA = "mp3_with_metadata"

    @property
    def content_type(self):
        if self is AudioFormat.WEBM_OPUS_HIGH:
            return "audio/webm"
        elif self is AudioFormat.WEBM_OPUS_LOW:
            return "audio/webm"
        elif self is AudioFormat.MP3_WITH_METADATA:
            return "audio/mp3"
        else:
            raise ValueError
