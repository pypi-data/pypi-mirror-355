import logging

from .artist import create_artist_url, get_artist_page_html, create_music_objects
from .network import NetworkHandler
from .database import Database
from .utils.storage import ensure_storage_directory
from .utils.errors import LyricallyDatabaseError, LyricallyError

logger = logging.getLogger(__name__)


class Lyrically:
    """A class to handle the discography scraping process."""

    def __init__(self, use_proxies: bool = False) -> None:
        """
        Initialize the Lyrically instance.

        Args:
            use_proxies (bool): The indication from the user on proxy usage.
        """
        self.use_proxies = use_proxies
        self.logs_dir, self.db_path, self.proxies_path = ensure_storage_directory()
        self.db = Database(self.db_path)
        self.network_handler = NetworkHandler(self.db, use_proxies, self.proxies_path)

    async def get_discography(self, artist_name: str) -> None:
        """
        Retreive the discography of an artist.

        Args:
            artist_name (str): The name of the artist whose discography will be obtained.
        """
        # Initialize DB connection and tables
        logger.info("Attempting to create DB instance.")
        try:
            await self.db.create()
            logger.info("DB instance has been created.")
        except Exception as e:
            msg = f"Failed to initialize DB: {e}"
            logger.exception(msg)
            raise LyricallyDatabaseError(msg) from e

        logger.info("Fetching discoraphy metadata for artist: '%s'", artist_name)

        # Get artist page html
        logger.info("Creating artist URL for '%s'", artist_name)
        artist_url = create_artist_url(artist_name)
        logger.info("Artist URL for %s was created. %s", artist_name, artist_url)

        logger.info("Fetching artist's page from %s", artist_url)
        artist_page_html = await get_artist_page_html(self.network_handler, artist_url)
        logger.info("Artist's page has been retrieved from %s.", artist_url)

        # Create Artist, Album & Track objects
        logger.info("Creating artist, album and track objects.")
        self.artist = create_music_objects(artist_page_html, artist_url)
        logger.info("Artist, Album & Tracks with metadata have been created.")

        # Store Artist, Album & Track objects in DB
        logger.debug("Attempting to store Artist, Album & Track objects in DB.")
        await self.db.add_artist(self.artist)
        logger.debug("Artist, Album & Track objects were stored in DB.")

        logger.info("Discography metadata fetching process has been completed.")

        # Start the lyric fetching process
        logger.info("Starting lyric fetching process.")

        tracks = [track for album in self.artist.albums for track in album.tracks]

        if tracks:
            if self.use_proxies:
                await self.network_handler.fetch_track_lyrics_asynchronously(tracks)
            else:
                await self.network_handler.fetch_track_lyrics_synchronously(tracks)
        else:
            msg = f"No track objects were created for {self.artist.name}"
            logger.error(msg)
            raise LyricallyError(msg)

        logger.info("Lyric fetching process completed.")
        logger.info("Discography processing for %s has finished.", self.artist.name)

    async def shutdown(self) -> None:
        """Close any remaining open instances."""
        logger.info("Shutting down database connection.")

        if self.db:
            await self.db.close()
            self.db = None
            logger.info("Database connection closed.")
        else:
            logger.info("No active database connection to shut down.")
