import logging
import asyncio
from pathlib import Path

import aiosqlite

from .create import create_connection, create_tables
from .add import add_artist
from .update import update_track_lyrics
from ..utils.errors import LyricallyDatabaseError
from ..utils.models import Artist

logger = logging.getLogger(__name__)


class Database:
    """A class to handle all of the database operations."""

    def __init__(self, db_path: Path) -> None:
        """
        Initialize the database instance.

        Args:
            db_path (Path): The location where the database should be stored.
        """
        self.db_path = db_path
        self.db_lock = asyncio.Lock()
        self.conn = None

        logger.debug("Raw database instance created for path: %s", self.db_path)

    async def close(self) -> None:
        """Close the database connection if it is open."""
        async with self.db_lock:
            if self.conn:
                logger.debug("Closing database connection for %s", self.db_path)

                try:
                    await self.conn.close()
                    logger.info("Database connection closed for %s", self.db_path)
                    self.conn = None
                except aiosqlite.Error as e:
                    self.conn = None
                    msg = f"Error closing database connection {self.db_path}: {e}"
                    logger.exception(msg)
                    raise LyricallyDatabaseError(msg) from e
            else:
                logger.debug("Attempted to close DB connection, but it wasn't open.")

    async def create(self) -> None:
        """Handle the asynchronous creation of the DB connection and schema."""
        async with self.db_lock:
            self.conn = await create_connection(self.db_path)
            await create_tables(self.conn)

        logger.debug("Database instance has been setup.")

    async def add_artist(self, artist: Artist) -> None:
        """
        Handle the asychronous addition of an artist to the DB.

        Args:
        artist (Artist): The artist to add to the database.
        """
        async with self.db_lock:
            await add_artist(self.conn, artist)

    async def update_track_lyrics(self, lyrics: str, url: str) -> None:
        """
        Handle the asychronous updating of a track's lyrics in the DB.

        Args:
        lyrics (str): The lyrics to store in the database.
        url (str): The URL of track.
        """
        async with self.db_lock:
            await update_track_lyrics(self.conn, lyrics, url)
