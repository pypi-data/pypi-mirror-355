import logging
from typing import Tuple

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_request(page_html_text: str, url: str) -> Tuple[int, BeautifulSoup | None]:
    """
    Parse and validate the webpage returned by the request.

    Args:
        page_html_text (str): The webpage HTML to validate.
        url (str): The URL to the webpage.

    Returns:
        Tuple[int, BeautifulSoup | None]: A tuple containing an error code, the parsed page html or None.
    """
    # Validate the status of the webpage
    if page_html_text:
        page_html = BeautifulSoup(page_html_text, "lxml")
        title = page_html.find("title")

        if title:
            title_text = title.get_text()

            if "Access Denied" in title or "request for access" in title_text:
                logger.error("Access denied for %s", url)
                return (2, None)
            else:
                return (0, page_html)
        else:
            logger.error("No title element was found on %s", url)
    else:
        logger.error("Page was not retrieved.")

    return (1, None)


def parse_song_lyrics(lyric_page_html: BeautifulSoup, url: str) -> str | None:
    """
    Parse lyrics from the lyric page HTML.

    Args:
        lyric_page_html (BeautifulSoup): The page HTML that contains the song lyrics.
        url (str): The URL of the page containing the page HTML.

    Returns:
        str | None: A string representing the lyrics, otherwise None.
    """
    logger.debug("Attempting to parse lyrics from %s", url)

    try:
        center_div = lyric_page_html.find(
            "div", class_="col-xs-12 col-lg-8 text-center"
        )
        if not center_div:
            logger.error("Could not find central text div from %s", url)
            return None

        lyrics_div = None
        possible_divs = center_div.find_all("div", recursive=False)
        for div in possible_divs:
            if not div.has_attr("class") and not div.has_attr("id"):
                lyrics_div = div
                break

        if lyrics_div:
            raw_lyrics = lyrics_div.get_text(separator="\n", strip=True)
            cleaned_lyrics = []

            for line in raw_lyrics.splitlines():
                if line.strip():
                    pass
            cleaned_lyrics = "\n".join(
                line for line in raw_lyrics.splitlines() if line.strip()
            )

            if not cleaned_lyrics:
                logger.error("Found lyrics div but extracted empty lyrics from %s", url)
                return None

            logger.debug("Successfully parsed lyrics from %s", url)
            return cleaned_lyrics
        else:
            logger.error(
                "Could not find any suitable lyrics container div from %s", url
            )
            return None

    except Exception as e:
        logger.exception("Error parsing lyrics HTML from %s", url)
        return None
