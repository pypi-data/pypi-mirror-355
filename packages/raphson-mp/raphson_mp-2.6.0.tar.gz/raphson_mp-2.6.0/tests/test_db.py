import shutil
import subprocess
import time
from pathlib import Path
from tempfile import mkdtemp, mktemp
from threading import Thread

from raphson_mp import db, settings
from tests import set_dirs


def test_migrate():
    temp_fresh = Path(mkdtemp("test_migrate_fresh"))
    temp_migrate = Path(mkdtemp("test_migrate_migrate"))
    try:
        settings.data_dir = temp_fresh
        # Test database initialization completes without errors (e.g. no SQL syntax errors)
        db.migrate()

        # Make sure auto vacuum is enabled
        for db_name in db.DATABASE_NAMES:
            with db._get_connection(db_name, True) as conn:
                auto_vacuum = conn.execute("PRAGMA auto_vacuum").fetchone()[0]
                assert auto_vacuum == 2

        settings.data_dir = temp_migrate

        # Initialize database how it would be when the migration system was first introduced
        # Not a great test because the tables have no content, but it's better than nothing.
        # db_version_0 files obtained from:
        # https://codeberg.org/raphson/music-server/src/commit/2c501187/src/sql
        for db_name in db.DATABASE_NAMES:
            with db._get_connection(db_name, False, should_exist=False) as conn:
                conn.executescript(
                    (Path(__file__).parent / "db_version_0" / f"{db_name}.sql").read_text(encoding="utf-8")
                )
                conn.executescript("ANALYZE;")

        # Run through all migrations
        db.migrate()

        # Check that database is up to date
        with db._get_connection("meta", True) as conn:
            version = conn.execute("SELECT version FROM db_version").fetchone()[0]
            assert version == len(db.get_migrations())

        # Make sure the migrated tables are equal to fresh tables
        for db_name in db.DATABASE_NAMES:
            command = ["sqldiff", "--schema", Path(temp_fresh, f"{db_name}.db"), Path(temp_migrate, f"{db_name}.db")]
            output = subprocess.check_output(command)
            assert output == b"", output.decode()
    finally:
        set_dirs()  # restore original data directory settings
        shutil.rmtree(temp_fresh)
        shutil.rmtree(temp_migrate)


def test_version():
    assert db.get_version().startswith("3.")


def test_write_read():
    """
    This tests whether a read-only database connection sees changes made by a
    different connection, without needing to re-open the read-only database connection.
    """
    test_db = mktemp()

    with db._get_connection(test_db, False, should_exist=False) as conn:
        conn.execute("CREATE TABLE test (test TEXT)")

    def reader():
        with db._get_connection(test_db, True) as conn:
            for _i in range(20):
                row = conn.execute("SELECT * FROM test").fetchone()
                if row:
                    assert row[0] == "hello"
                    return
                time.sleep(0.1)

        raise ValueError("did not read value")

    thread = Thread(target=reader)
    thread.start()
    time.sleep(0.5)
    with db._get_connection(test_db, False) as conn:
        conn.execute('INSERT INTO test VALUES ("hello")')
    thread.join()
