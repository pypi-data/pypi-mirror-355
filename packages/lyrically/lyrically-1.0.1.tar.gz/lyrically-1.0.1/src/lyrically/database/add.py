import logging

import aiosqlite

from ..utils.models import Artist, Album, Track
from ..utils.errors import LyricallyDatabaseError

logger = logging.getLogger(__name__)


async def add_artist(conn: aiosqlite.Connection, artist: Artist) -> None:
    """
    Add an artist to the DB.

    Args:
        artist (Artist): The artist to add to the database.
    """

    logger.debug("Attempting to add artist '%s' in DB.", artist.name)
    cursor = None

    try:
        cursor = await conn.cursor()

        # Insert the artist into the DB
        await cursor.execute(
            "INSERT OR IGNORE INTO artists (name, url) VALUES (?, ?)",
            (artist.name, artist.url),
        )

        # Retrieve ID of the artist
        await cursor.execute("SELECT id FROM artists WHERE name = ?", (artist.name,))
        result = await cursor.fetchone()

        if result:
            artist_id = result[0]
            logger.debug(
                "Artist '%s' (ID: %s) is present in the DB. Adding associated albums.",
                artist.name,
                artist_id,
            )

            # Add artist's associated albums
            if artist.albums:
                for album in artist.albums:
                    await add_album(cursor, artist_id, album)

            else:
                logger.debug("No albums associated with artist '%s'.", artist.name)

            await conn.commit()
            logger.info(
                "Artist '%s' (ID: %s) associated albums and tracks are present in the DB.",
                artist.name,
                artist_id,
            )
        else:
            msg = f"Artist insertion failed. Could not retrieve ID for '{artist.name}'."
            logger.error(msg)
            raise LyricallyDatabaseError(msg)

    except aiosqlite.Error as e:
        msg = f"Database error processing artist '{artist.name}': {e}"
        logger.exception(msg)

        try:
            await conn.rollback()
        except Exception as rb_e:
            logger.error(f"Rollback failed: {rb_e}")

        raise LyricallyDatabaseError(msg) from e

    except Exception as e:
        msg = f"Unexpected error processing artist '{artist.name}': {e}"
        logger.exception(msg)

        try:
            await conn.rollback()
        except Exception as rb_e:
            logger.error(f"Rollback failed: {rb_e}")

        raise LyricallyDatabaseError(msg) from e

    finally:
        if cursor:
            await cursor.close()


async def add_album(cursor: aiosqlite.Cursor, artist_id: int, album: Album) -> None:
    """
    Add an album to the DB.

    Args:
        artist_id (int): The ID of the artist to attach this album to.
        album (Album): The Album object that will be stored.
    """
    logger.debug(
        "Attempting to add album '%s' for artist ID %d.", album.title, artist_id
    )
    try:
        # Insert the album into the DB
        await cursor.execute(
            "INSERT OR IGNORE INTO albums (artist_id, title) VALUES (?, ?)",
            (artist_id, album.title),
        )
        # Retrieve the ID of the album
        await cursor.execute(
            "SELECT id FROM albums WHERE artist_id = ? AND title = ?",
            (artist_id, album.title),
        )
        result = await cursor.fetchone()

        if result:
            album_id = result[0]
            logger.debug(
                "Album '%s' (ID: %s) is present in the DB. Adding associated tracks.",
                album.title,
                album_id,
            )

            # Add album's associated tracks
            if album.tracks:
                for track in album.tracks:
                    await add_track(cursor, album_id, track)

            else:
                logger.debug("No tracks associated with album '%s'.", album.title)

        else:
            msg = f"Album insertion failed. Could not retrieve ID for '{album.title}'."
            logger.error(msg)
            raise LyricallyDatabaseError(msg)

    except aiosqlite.Error as e:
        msg = f"Database error processing album '{album.title}': {e}"
        logger.exception(msg)
        raise LyricallyDatabaseError(msg) from e

    except Exception as e:
        msg = f"Unexpected error processing album '{album.title}': {e}"
        logger.exception(msg)
        raise LyricallyDatabaseError(msg) from e


async def add_track(cursor: aiosqlite.Cursor, album_id: int, track: Track) -> None:
    """
    Add a Track to the database.

    Args:
        cursor (aiosqlite.Cursor): The cursor that will be used for this transacation.
        album_id (int): The ID of the artist to attach this track to.
        track (Track): The Track object that will be stored.
    """
    logger.debug("Attempting to add track '%s' for album ID %d.", track.title, album_id)
    try:
        # Insert the track into the DB
        await cursor.execute(
            "INSERT OR IGNORE INTO tracks (album_id, title, url, lyrics) VALUES (?, ?, ?, ?)",
            (album_id, track.title, track.url, track.lyrics),
        )
        await cursor.execute("SELECT id FROM tracks WHERE url = ?", (track.url,))
        result = await cursor.fetchone()

        if result:
            track_id = result[0]
            logger.debug(
                "Track '%s' (ID: %s) is present in the DB.", track.title, track_id
            )

        else:
            msg = f"Track insertion failed. Could not retrieve ID for '{track.title}'."
            logger.error(msg)
            raise LyricallyDatabaseError(msg)

    except aiosqlite.Error as e:
        msg = f"Database error processing track '{track.title}': {e}"
        logger.exception(msg)
        raise LyricallyDatabaseError(msg) from e

    except Exception as e:
        msg = f"Unexpected error processing track '{track.title}': {e}"
        logger.exception(msg)
        raise LyricallyDatabaseError(msg) from e
