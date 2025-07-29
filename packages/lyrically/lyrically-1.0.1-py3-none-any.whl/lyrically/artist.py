import logging
import unicodedata
import re
from urllib.parse import urljoin
from typing import List

import aiohttp
from bs4 import BeautifulSoup

from .config import BASE_URL, HEADERS
from .network import NetworkHandler
from .utils.models import Artist, Album, Track
from .utils.errors import LyricallyError, LyricallyRequestError, LyricallyParseError

logger = logging.getLogger(__name__)


def create_artist_url(artist_name: str) -> str:
    """
    Create an URL for a specific artist.

    Args:
        artist_name (str): The name of the music artist.

    Returns:
        artist_url (str): The URL to the artist's page.
    """
    # Normalize accented characters & perform common substitutions
    logger.debug("Attempting to clean artist name.")

    try:
        normalized = unicodedata.normalize("NFKD", artist_name)
        ascii_name = normalized.encode("ASCII", "ignore").decode("utf-8")
    except Exception as e:
        msg = f"Error normalizing artist name '{artist_name}': {e}"
        logger.exception(msg)
        raise LyricallyError(msg)

    substituted_name = ascii_name.replace("!", "i").replace("$", "s")
    cleaned = re.sub(r"[^a-z0-9]", "", substituted_name.lower())

    if not cleaned:
        msg = f"Artist name '{artist_name}' resulted in empty string after cleaning."
        logger.error(msg)
        raise LyricallyError(msg)

    logger.debug("Cleaned artist name: %s", cleaned)

    # Construct URL
    logger.debug("Attempting to construct artist URL.")

    first_char = cleaned[0]

    if first_char.isdigit():
        prefix = "19"
    elif first_char.isalpha():
        prefix = first_char
    else:
        msg = f"Cleaned artist name '{cleaned}' started with unexpected character '{first_char}'"
        logger.error(msg)
        raise LyricallyError(msg)

    full_path = f"/{prefix}/{cleaned}.html"
    artist_url = urljoin(BASE_URL, full_path)

    logger.debug("Generated URL %s for the artist '%s'", artist_url, artist_name)
    return artist_url


async def get_artist_page_html(
    network_handler: NetworkHandler, artist_url: str
) -> BeautifulSoup:
    """
    Fetch the HTML of an artist's discography page.

    Args:
        artist_url (str): The URL of the page HTML to fetch.

    Returns:
        A BeautifulSoup object that contains the requested page HTML as
        an object.
    """
    artist_page_html = None
    logger.debug("Fetching page from %s", artist_url)

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        artist_page_html = await network_handler.send_request(session, artist_url)

    if artist_page_html:
        logger.debug("Page was fetched from %s", artist_url)
        return artist_page_html
    else:
        msg = f"Error when trying to retrieve the artist page: {artist_url}"
        logger.error(msg)
        raise LyricallyRequestError(msg)


def create_artist_object(artist_page_html: BeautifulSoup, url: str) -> Artist:
    """
    Create the artist object.

    Args:
        artist_page_html (BeautifulSoup): The soup object representing the
        artist's discography page.
        url (str): A string containing the URL to the artist's discography page.

    Returns:
        artist (Artist): An artist object.
    """
    # Get offical artist name
    logger.debug("Attempting to extract official artist name from title tag.")
    try:
        title_text = artist_page_html.find("title").get_text()
        official_artist_name = title_text.split(" Lyrics")[0]
        logger.info("Official artist name found: '%s'", official_artist_name)
    except AttributeError:
        msg = f"Could not find title tag on page {url} to extract artist name."
        logger.error(msg)
        raise LyricallyParseError(msg)

    # Create artist object
    artist = Artist(official_artist_name, url)
    logger.debug("Artist object was created: %s", artist)

    return artist


def create_album_track_objects(
    artist_page_html: BeautifulSoup, url: str
) -> List[Album]:
    """
    Create the Album and Track objects.

    Args:
        artist_page_html (BeautifulSoup): The soup object representing the
        artist's discography page.
        url (str): A string containing the URL to the artist's discography page.

    Returns:
        albums (List[Album]): A list of Album objects.
    """
    logger.debug("Attempting to parse the discography metadata.")
    music_containers = artist_page_html.find("div", {"id": "listAlbum"})

    if music_containers is None:
        msg = f"Could not find listAlbum div for {url}."
        logger.error(msg)
        raise LyricallyParseError(msg)

    music_container_divs = music_containers.find_all("div")

    albums = []
    current_album = None
    previous_track = None

    for element in music_container_divs:
        if element.has_attr("class"):
            if "album" in element["class"]:
                # Store the current album if there is one before creating a new object
                if current_album:
                    if current_album.tracks:
                        albums.append(current_album)
                        logger.debug(
                            "Finished processing album: '%s' (%d tracks)",
                            current_album.title,
                            len(current_album.tracks),
                        )
                    else:
                        logger.error("Skipping empty album: '%s'", current_album.title)

                album_title_tag = element.find("b")
                if album_title_tag:
                    album_title = album_title_tag.get_text().strip()

                    if album_title.startswith('"') and album_title.endswith('"'):
                        album_title = album_title[1:-1]

                    current_album = Album(album_title)
                    logger.debug("Started processing album: '%s'", current_album.title)
                else:
                    logger.error(
                        "Found album div without title: %s", element.prettify()
                    )
                    current_album = None
            elif "listalbum-item" in element["class"]:
                # Create a track and store it within the current album object
                raw_track_attrs = element.find("a")

                if raw_track_attrs:
                    track_title = raw_track_attrs.get_text()
                    track_url = urljoin(BASE_URL, raw_track_attrs.get("href"))

                    track = Track(track_title, track_url)
                    current_album.tracks.append(track)

                    logger.debug("Track object named %s has been created.", track_title)
                    previous_track = track
                else:
                    msg = f"Could not find raw track attributes for current track. Previous track: {previous_track}"
                    logger.error(msg)
                    raise LyricallyParseError(msg)

    # Add the last album if it exists and has tracks
    if current_album and current_album.tracks:
        albums.append(current_album)
        logger.debug(
            "Finished processing album: '%s' (%d tracks)",
            current_album.title,
            len(current_album.tracks),
        )
        current_album = None
    elif current_album:
        logger.debug("Skipping empty final album: '%s'", current_album.title)

    logger.debug("Finished parsing discography metadata.")

    return albums


def create_music_objects(artist_page_html: BeautifulSoup, url: str) -> Artist:
    """
    Handle the operations of creating Artist, Album and Track objects.

    Args:
        artist_page_html (BeautifulSoup): The soup object representing the
        artist's discography page.
        url (str): A string containing the URL to the artist's discography page.

    Returns:
        artist (Artist): An artist object.
    """
    artist = create_artist_object(artist_page_html, url)
    albums = create_album_track_objects(artist_page_html, url)

    for album in albums:
        artist.albums.append(album)

    return artist
