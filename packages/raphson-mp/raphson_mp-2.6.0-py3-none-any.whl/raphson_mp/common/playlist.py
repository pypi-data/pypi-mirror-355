from dataclasses import dataclass


@dataclass
class Playlist:
    name: str
    track_count: int
    favorite: bool
    write: bool
