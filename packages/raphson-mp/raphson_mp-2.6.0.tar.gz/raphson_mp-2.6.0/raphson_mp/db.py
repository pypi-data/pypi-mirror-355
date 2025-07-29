import logging
import os
import sqlite3
import sys
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from pathlib import Path
from sqlite3 import Connection
from typing import NotRequired, TypedDict, Unpack

from raphson_mp import settings
from raphson_mp.util import log_duration

log = logging.getLogger(__name__)


DATABASE_NAMES = ["cache", "music", "offline", "meta"]
CACHED_CONNECTIONS: dict[str, Connection] = {}


def _db_path(db_name: str) -> Path:
    return settings.data_dir / (db_name + ".db")


def _new_connection(db_name: str, read_only: bool = False, should_exist: bool = True):
    with log_duration(f"open db {db_name} read_only={read_only}"):
        path = _db_path(db_name)
        if should_exist and not path.is_file():
            raise RuntimeError("database file does not exist: " + path.absolute().as_posix())
        elif not should_exist and path.is_file():
            raise RuntimeError("database file already exists: " + path.absolute().as_posix())
        db_uri = f"file:{path.as_posix()}"
        if read_only:
            db_uri += "?mode=ro"
        if sys.version_info >= (3, 12):
            conn = sqlite3.connect(db_uri, uri=True, timeout=30.0, autocommit=True)  # pyright: ignore[reportUnreachable]
        else:
            conn = sqlite3.connect(db_uri, uri=True, timeout=30.0)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA temp_store = MEMORY")  # https://www.sqlite.org/pragma.html#pragma_temp_store
        conn.execute("PRAGMA synchronous = NORMAL")  # https://www.sqlite.org/pragma.html#pragma_synchronous

    return conn


class ConnectOptions(TypedDict):
    read_only: NotRequired[bool]
    should_exist: NotRequired[bool]
    no_cache: NotRequired[bool]


def _close(conn: Connection, read_only: bool):
    try:
        if not read_only:
            #  -- optimize
            # > Applications with short-lived database connections should run "PRAGMA optimize;" once, just prior
            # to closing each database connection.
            # https://www.sqlite.org/pragma.html#pragma_optimize

            #  -- incremental_vacuum
            # Unmap deleted pages. The number of vacuumed pages is limited to prevent this function from blocking for
            # too long. Max 4096 pages = 16MiB. For some reason, incremental_vacuum only works in executescript(),
            # not regular execute()

            conn.executescript(
                """
                PRAGMA optimize;
                PRAGMA incremental_vacuum(4096);
                """
            )
    finally:
        conn.close()


@contextmanager
def _get_connection(db_name: str, read_only: bool = False, should_exist: bool = True, no_cache: bool = False):
    if not no_cache and settings.server is not None and read_only:
        # when running server, use single database connection
        conn = CACHED_CONNECTIONS.get(db_name)
        if conn is None:
            conn = _new_connection(db_name, read_only, should_exist=should_exist)
            conn.execute("BEGIN")
            CACHED_CONNECTIONS[db_name] = conn

            async def close():
                _close(conn, read_only)

            settings.server.cleanup.append(close)

        if read_only:
            # Sometimes (rarely), the persistent read-only connection would have an outdated view of the database. To
            # me this is surprising, but according to the documentation it is expected behaviour:
            # > In WAL mode, SQLite exhibits "snapshot isolation". When a read transaction starts, that reader
            # > continues to see an unchanging "snapshot" of the database file as it existed at the moment in time
            # > when the read transaction started. Any write transactions that commit while the read transaction is
            # > active are still invisible to the read transaction, because the reader is seeing a snapshot of database
            # > file from a prior moment in time.
            # From: https://www.sqlite.org/isolation.html
            # Work around the issue by starting a fresh read transaction every time a "new" connection is requested
            # try:
            conn.execute("COMMIT")
            conn.execute("BEGIN")

        yield conn
    else:
        # when no server is running, or the connection must be read-write, return new database
        # connection and close it afterwards
        conn = _new_connection(db_name, read_only, should_exist=should_exist)
        try:
            yield conn
        finally:
            _close(conn, read_only)


def db_size(db_name: str):
    return os.stat(_db_path(db_name)).st_size


def connect(**kwargs: Unpack[ConnectOptions]) -> AbstractContextManager[Connection]:
    """
    Create new SQLite database connection to main music database
    """
    return _get_connection("music", **kwargs)


def cache(**kwargs: Unpack[ConnectOptions]) -> AbstractContextManager[Connection]:
    """
    Create new SQLite database connection to cache database
    """
    return _get_connection("cache", **kwargs)


def offline(**kwargs: Unpack[ConnectOptions]) -> AbstractContextManager[Connection]:
    """
    Create new SQLite database connection to offline database
    """
    return _get_connection("offline", **kwargs)


def create_databases() -> None:
    """
    Initialize SQLite databases using SQL scripts
    """
    for db_name in DATABASE_NAMES:
        log.debug("Creating database: %s", db_name)
        with _get_connection(db_name, False, should_exist=False) as conn:
            conn.execute("PRAGMA auto_vacuum = INCREMENTAL")  # must be set before any tables are created
            conn.execute("PRAGMA journal_mode = WAL")  # https://www.sqlite.org/wal.html
            conn.executescript((settings.init_sql_dir / f"{db_name}.sql").read_text(encoding="utf-8"))
            conn.executescript("ANALYZE;")

    with _get_connection("meta", False) as conn:
        migrations = get_migrations()
        assert migrations
        version = migrations[-1].to_version

        log.info("Setting initial database version to %s", version)

        conn.execute("INSERT INTO db_version VALUES (?)", (version,))


@dataclass
class Migration:
    file_name: str
    to_version: int
    db_name: str

    def run(self) -> None:
        """Execute migration file"""
        with _get_connection(self.db_name, False) as conn:
            conn.executescript((settings.migration_sql_dir / self.file_name).read_text(encoding="utf-8"))
            conn.executescript("ANALYZE;")


def get_migrations() -> list[Migration]:
    migration_file_names = [path.name for path in settings.migration_sql_dir.iterdir() if path.name.endswith(".sql")]

    migrations: list[Migration] = []

    for i, file_name in enumerate(sorted(migration_file_names)):
        name_split = file_name.split("-")
        assert len(name_split) == 2, name_split
        to_version = int(name_split[0])
        db_name = name_split[1][:-4]
        assert i + 1 == int(name_split[0]), f"{i} | {int(name_split[0])}"
        assert db_name in DATABASE_NAMES, db_name
        migrations.append(Migration(file_name, to_version, db_name))

    return migrations


def get_version() -> str:
    with sqlite3.connect(":memory:") as conn:
        version = conn.execute("SELECT sqlite_version()").fetchone()[0]
    conn.close()
    return version


def optimize():
    log.info("optimizing databases")
    for name in DATABASE_NAMES:
        with _get_connection(name, False, True) as conn:
            #  -- wal_checkpoint
            # Clean up wal/shm files, without blocking. Can only clean up parts of the WAL file that were written
            # before any reader has opened a connection.
            # > PASSIVE: Checkpoint as many frames as possible without waiting for any database readers or writers to
            # > finish.
            # https://www.sqlite.org/pragma.html#pragma_wal_checkpoint
            #
            # > A checkpoint operation takes content from the WAL file and transfers it back into the original database
            # > file. A checkpoint can run concurrently with readers, however the checkpoint must stop when it reaches
            # > a page in the WAL that is past the end mark of any current reader. The checkpoint has to stop at that
            # > point because otherwise it might overwrite part of the database file that the reader is actively using.
            # > The checkpoint remembers (in the wal-index) how far it got and will resume transferring content from
            # > the WAL to the database from where it left off on the next invocation.
            # >
            # > Thus a long-running read transaction can prevent a checkpointer from making progress. But presumably
            # > every read transaction will eventually end and the checkpointer will be able to continue.
            # https://www.sqlite.org/wal.html

            conn.executescript(
                """
                PRAGMA optimize=0x10002;
                PRAGMA wal_checkpoint(TRUNCATE);
                """
            )


def migrate() -> None:
    log.debug("Using SQLite version: %s", get_version())

    if not (settings.data_dir / "meta.db").exists():
        log.info("Creating databases")
        create_databases()
        return

    with _get_connection("meta", True) as conn:
        version_row = conn.execute("SELECT version FROM db_version").fetchone()
        if version_row:
            version = version_row[0]
        else:
            log.error("Version missing from database. Cannot continue.")
            sys.exit(1)

    migrations = get_migrations()

    if len(migrations) < version:
        log.error("Database version is greater than number of migration files")
        sys.exit(1)

    pending_migrations = migrations[version:]
    if len(pending_migrations) == 0:
        log.info("No pending migrations")
    else:
        for migration in pending_migrations:
            log.info("Running migration to version %s", migration.to_version)
            migration.run()
            with _get_connection("meta", False) as conn:
                conn.execute("UPDATE db_version SET version=?", (migration.to_version,))
