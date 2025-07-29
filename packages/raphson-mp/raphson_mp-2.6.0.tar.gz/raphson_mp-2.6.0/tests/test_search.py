from raphson_mp import db, search

# low quality tests, but at least they ensure the SQL queries don't contain syntax errors


def test_search_tracks():
    with db.connect(read_only=True) as conn:
        search.search_tracks(conn, "test")


def test_albums():
    with db.connect(read_only=True) as conn:
        search.search_albums(conn, "test")
