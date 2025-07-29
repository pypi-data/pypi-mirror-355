import logging
import time
import asyncio
from typing import List

import aiohttp
import aiosqlite
from bs4 import BeautifulSoup

from .config import HEADERS, REQUEST_DELAY_TIME, MAX_CONCURRENT_REQUESTS
from .parser import parse_request, parse_song_lyrics
from .utils.models import Track
from .utils.errors import LyricallyRequestError

logger = logging.getLogger(__name__)


class NetworkHandler:
    """A class to handle network operations."""

    def __init__(
        self, db: aiosqlite.Connection, use_proxies: bool, proxy_path: str
    ) -> None:
        """
        Initialize the network handler.

        Args:
            db (aiosqlite.Connection): The database connection.
            use_proxies (bool): User's request to use proxies or not.
            proxy_path (str): The location to the proxies text file.
        """
        self.db = db
        self.use_proxies = use_proxies
        self.proxy_manager = {"green": {}, "yellow": set(), "red": set()}
        self.proxies_lock = asyncio.Lock()
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        self.store_lyrics = False

        # Setup proxy manager
        if self.use_proxies:
            with open(proxy_path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        # Default timestamp for each proxy is 0.
                        proxy = f"http://{line}"
                        self.proxy_manager["green"][proxy] = 0

    async def send_request(
        self, session: aiohttp.ClientSession, url: str
    ) -> BeautifulSoup | None:
        """
        Handle the sending of HTTP requests.

        Args:
            session (aiohttp.ClientSession): The session object to send the request with.
            url (str): The URL to send the request to.

        Returns:
            BeautifulSoup | None: Parsed HTML content, or None if the request fails.
        """
        logger.debug("Attempting GET request for %s", url)

        if self.use_proxies:
            return await self.send_request_async(session, url)

        else:
            return await self.send_request_sync(session, url)

    async def send_request_sync(self, session, url) -> BeautifulSoup | None:
        """
        Send request synchronously with no proxies.

        Args:
            session (aiohttp.ClientSession): The session object to send the request with.
            url (str): The URL to send the request to.

        Returns:
            BeautifulSoup | None: Parsed HTML content, or None if the request fails.
        """
        try:
            async with session.get(url) as response:
                page_html_text = await response.text()
                _, page_html = parse_request(page_html_text, url)

                if page_html:
                    return page_html
                else:
                    logger.error("Page from %s could not be fetched.", url)

        except aiohttp.ClientError as e:
            logger.exception("Error fetching page %s: %s", url, e)
        except Exception as e:
            logger.exception("Error obtaining the page HTML for %s, %s", url, e)

    async def send_request_async(self, session, url) -> BeautifulSoup | None:
        """
        Send request asynchronously with proxies.

        Args:
            session (aiohttp.ClientSession): The session object to send the request with.
            url (str): The URL to send the request to.

        Returns:
            BeautifulSoup | None: Parsed HTML content, or None if the request fails.
        """
        async with self.semaphore:
            selected_proxy = None

            while not selected_proxy:
                logger.debug("Fetching a proxy for this request.")
                retry_proxy_selection = False

                async with self.proxies_lock:
                    # Check status of current proxies
                    if (
                        len(self.proxy_manager["green"])
                        + len(self.proxy_manager["yellow"])
                        == 0
                    ):
                        msg = "No proxies are available."
                        logger.error(msg)
                        raise LyricallyRequestError(msg)
                    elif (
                        len(self.proxy_manager["green"]) == 0
                        and len(self.proxy_manager["yellow"]) > 0
                    ):
                        logger.debug(
                            "All proxies are currently being used, waiting before retrying."
                        )
                        retry_proxy_selection = True
                    else:
                        # Select a proxy
                        for proxy, timestamp in self.proxy_manager["green"].items():
                            # Proxy shouldn't be used within the last timeframe of REQUEST_DELAY_TIME
                            if (time.time() - timestamp) >= REQUEST_DELAY_TIME:
                                self.proxy_manager["yellow"].add(proxy)
                                del self.proxy_manager["green"][proxy]
                                selected_proxy = proxy
                                break
                            else:
                                logger.debug(
                                    "Proxy %s has been recently used. Trying a new one.",
                                    proxy,
                                )

                if retry_proxy_selection:
                    await asyncio.sleep(5)
                    continue
            try:
                async with session.get(url, proxy=selected_proxy) as response:
                    page_html_text = await response.text()
                    err, page_html = parse_request(page_html_text, url)

                # Off-load current proxy
                if err == 2:
                    async with self.proxies_lock:
                        self.proxy_manager["yellow"].remove(selected_proxy)
                        self.proxy_manager["red"].add(selected_proxy)
                else:
                    async with self.proxies_lock:
                        self.proxy_manager["green"][selected_proxy] = time.time()
                        self.proxy_manager["yellow"].remove(selected_proxy)

                if page_html is None:
                    logger.error("Page from %s could not be fetched.", url)
                    return None
                else:
                    if self.store_lyrics:
                        lyrics = parse_song_lyrics(page_html, url)

                        if lyrics:
                            await self.db.update_track_lyrics(lyrics, url)
                    else:
                        return page_html

            except aiohttp.ClientError as e:
                logger.exception("Error fetching page %s: %s", url, e)
            except Exception as e:
                logger.exception("Error obtaining the page HTML for %s, %s", url, e)

    async def fetch_track_lyrics_synchronously(self, tracks: List[Track]) -> None:
        """
        Fetch track lyrics synchronously.

        Args:
            tracks (List[Track]): The list of tracks to get the lyrics for.
        """
        logger.info("Starting synchronous lyric fetching for %d tracks.", len(tracks))

        async with aiohttp.ClientSession(headers=HEADERS) as session:
            for i, track in enumerate(tracks):
                logger.debug(
                    "Processing track %d/%d: '%s' (%s)",
                    i + 1,
                    len(tracks),
                    track.title,
                    track.url,
                )

                try:
                    logger.debug(
                        "Waiting %.1f seconds before requesting %s",
                        REQUEST_DELAY_TIME,
                        track.url,
                    )
                    time.sleep(REQUEST_DELAY_TIME)

                    lyric_page_html = await self.send_request(session, track.url)

                    if lyric_page_html:
                        lyrics = parse_song_lyrics(lyric_page_html, track.url)

                        if lyrics:
                            logger.debug(
                                "Lyrics parsed for track: '%s' (%s). Attempting to update DB.",
                                track.title,
                                track.url,
                            )
                            await self.db.update_track_lyrics(lyrics, track.url)
                        else:
                            logger.error(
                                "Failed to parse lyrics for '%s' (%s)",
                                track.title,
                                track.url,
                            )
                    else:
                        logger.error(
                            "Failed to retrieve lyric page HTML for track: '%s' (%s)",
                            track.title,
                            track.url,
                        )

                except Exception as e:
                    logger.exception(
                        "Unexpected error processing lyrics for track: '%s' (%s)",
                        track.title,
                        track.url,
                    )

    async def fetch_track_lyrics_asynchronously(self, tracks: List[Track]) -> None:
        """
        Fetch track lyrics asynchronously.

        Args:
            tracks (List[Track]): The list of tracks to get the lyrics for.
        """
        logger.info("Starting asynchronous lyric fetching for %d tracks.", len(tracks))

        self.store_lyrics = True

        async with aiohttp.ClientSession(headers=HEADERS) as session:
            tasks = [self.send_request(session, track.url) for track in tracks]
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.debug("All lyrics have been fetched.")
