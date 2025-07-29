import logging

import aiosqlite

from ..utils.errors import LyricallyDatabaseError

logger = logging.getLogger(__name__)


async def update_track_lyrics(
    conn: aiosqlite.Connection, lyrics: str, url: str
) -> None:
    """
    Update a track in the database with its lyrics.

    Args:
        conn (aiosqlite.Connection): The connection to commit transacations to.
        lyrics (str): The lyrics that will be stored.
        url (str): The URL of the track to attach these lyrics to.
    """
    logger.debug("Attempting to update lyrics for track URL: %s", url)
    cursor = None

    try:
        cursor = await conn.cursor()

        await cursor.execute(
            "UPDATE tracks SET lyrics = ? WHERE url = ?", (lyrics, url)
        )

        if cursor.rowcount > 0:
            await conn.commit()
            logger.debug("Successfully updated lyrics in DB for track (%s)", url)
        else:
            msg = f"Failed to update DB lyrics for track {url}."
            logger.error(msg)
            raise LyricallyDatabaseError(msg)

    except aiosqlite.Error as e:
        msg = f"Database error updating lyrics for track URL {url}: {e}"
        logger.exception(msg)

        try:
            await conn.rollback()
        except Exception as rb_e:
            logger.error(f"Rollback failed: {rb_e}")

        raise LyricallyDatabaseError(msg) from e

    except Exception as e:
        msg = f"Unexpected error updating lyrics for track URL {url}: {e}"
        logger.exception(msg)

        try:
            await conn.rollback()
        except Exception as rb_e:
            logger.error(f"Rollback failed: {rb_e}")

        raise LyricallyDatabaseError(msg) from e

    finally:
        if cursor:
            await cursor.close()
