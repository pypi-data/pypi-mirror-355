import logging
from pathlib import Path

import aiosqlite

from ..utils.errors import LyricallyDatabaseError

logger = logging.getLogger(__name__)


async def create_connection(db_path: Path) -> aiosqlite.Connection:
    """
    Create a database connection.

    Args:
        db_path (Path): The location where the database should be stored.

    Returns:
        aiosqlite.Connection | None: A database connection.
    """
    conn = None
    logger.debug("Attempting to establish database connection to %s.", db_path)

    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = await aiosqlite.connect(db_path, timeout=10.0)

        # Enable foreign key support
        await conn.execute("PRAGMA foreign_keys = ON;")

        logger.debug("Database connection established to %s.", db_path)
    except aiosqlite.Error as e:
        msg = f"Failed to connect to or configure database {db_path}: {e}"
        logger.exception(msg)
        raise LyricallyDatabaseError(msg) from e

    except Exception as e:
        if conn:
            try:
                await conn.close()
            except Exception:
                pass

        msg = f"Unexpected error during database connection/configuration for {db_path}: {e}"
        logger.exception(msg)
        raise LyricallyDatabaseError(msg) from e

    return conn


async def create_tables(conn: aiosqlite.Connection) -> None:
    """
    Create database tables.

    Args:
        conn (aiosqlite.Connection): The connection to the database.
    """
    logger.debug("Initializing database schema.")

    try:
        # Artists Table
        await conn.execute(
            """
                CREATE TABLE IF NOT EXISTS artists (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    url TEXT UNIQUE NOT NULL
                )
            """
        )
        logger.debug("Table 'artists' is present in DB.")

        # Albums Table
        await conn.execute(
            """
                CREATE TABLE IF NOT EXISTS albums (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    artist_id INTEGER NOT NULL,
                    FOREIGN KEY (artist_id) REFERENCES artists (id) ON DELETE CASCADE,
                    UNIQUE (artist_id, title)
                )
            """
        )
        logger.debug("Table 'albums' is present in DB.")

        # Tracks Table
        await conn.execute(
            """
                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    lyrics TEXT,
                    album_id INTEGER NOT NULL,
                    FOREIGN KEY (album_id) REFERENCES albums (id) ON DELETE CASCADE,
                    UNIQUE (album_id, title)
                )
            """
        )
        logger.debug("Table 'tracks' is present in DB.")

        await conn.commit()
        logger.info("Database schema initialization complete.")

    except aiosqlite.Error as e:
        msg = f"Failed to initialize database schema: {e}"
        logger.exception(msg)

        try:
            await conn.rollback()
            logger.info("Rollback attempted after schema initialization error.")
        except aiosqlite.Error as rb_e:
            logger.error(f"Rollback failed after schema init error: {rb_e}")

        raise LyricallyDatabaseError(msg) from e
