from pathlib import Path

from raphson_mp import db
from raphson_mp.music import filter_tracks, is_trashed, relpath_playlist


def test_relpath_playlist():
    assert relpath_playlist("RS") == "RS"
    assert relpath_playlist("RS/A/B") == "RS"


def test_is_trashed():
    assert not is_trashed(Path("test"))
    assert is_trashed(Path(".trash.test"))
    assert is_trashed(Path(".trash.test/test"))


def test_filter_tracks():
    # not a functional test, but ensures SQL has no syntax error
    with db.connect() as conn:
        for order in ["title", "ctime", "year", "random"]:
            for has_metadata in [False, True]:
                filter_tracks(
                    conn,
                    10,
                    0,
                    playlist="test",
                    artist="test",
                    album_artist="test",
                    album="test",
                    year=1000,
                    has_metadata=has_metadata,
                    order=order,
                )
