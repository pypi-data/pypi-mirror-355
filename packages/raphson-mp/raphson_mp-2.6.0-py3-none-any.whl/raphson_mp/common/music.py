from dataclasses import dataclass


@dataclass
class Album:
    name: str
    artist: str | None
    track: str # arbitrary track from the album, can be used to obtain a cover art image


@dataclass
class Artist:
    name: str
    track: str # arbitrary track from the artist, can be used to obtain an image


@dataclass
class Playlist:
    name: str
