# Lyrically

Lyrically is an asynchronous Python tool designed to scrape artist discographies and song lyrics from AZLyrics.com and store them locally in an SQLite database.

## Features

*   **Artist Discography Scraping:** Retrieves album and track listings for a given artist.
*   **Lyric Scraping:** Fetches and stores lyrics for each track.
*   **Metadata Storage:** Stores artist, album, and track data in an SQLite database.
*   **Asynchronous:** Uses `asyncio`, `aiohttp` and `aiosqlite` for efficient I/O operations.
*   **Proxy Support:** Option to route requests through proxies for lyric fetching.
*   **Robust Parsing:** Uses `BeautifulSoup` with the `lxml` parser.
*   **Logging:** Detailed logging of operations and errors.

## Installation

You can install `lyrically` directly from GitHub Releases or by cloning the repository.

### From GitHub Releases (Recommended)

1.  Go to the [Releases page](https://github.com/filming/lyrically/releases).
2.  Download the latest `.whl` file
3.  Install it using pip:
    ```bash
    pip install /path/to/downloaded/lyrically-X.Y.Z-py3-none-any.whl
    ```
    Replace `X.Y.Z` with the actual version number and `/path/to/downloaded/` with the correct path to the file.

### From Source (after cloning)

1.  Clone the repository:
    ```bash
    git clone https://github.com/filming/lyrically.git
    cd lyrically
    ```
2.  Install using pip:
    ```bash
    pip install .
    ```
    If you are developing the project, you might prefer an editable install:
    ```bash
    pip install -e .
    ```

## Usage

```python
import asyncio
from lyrically import Lyrically

async def main():
    # Initialize with use_proxies=True if you have configured proxies.txt
    scraper = Lyrically(use_proxies=False) 

    try:
        # Get and store discography (metadata and lyrics) for an artist
        await scraper.get_discography("Artist Name") # Replace "Artist Name"
        print(f"Successfully processed discography for Artist Name")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensure resources are cleaned up, especially the database connection
        await scraper.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

Upon first run, the script will create a `storage` directory in the project root (or use the one defined by `LYRICALLY_STORAGE_DIR` in `src/lyrically/config.py`, default is `storage/`). This directory will contain:

*   `logs/Lyrically.log`: The application log file (note the capitalization from your `logger.py`).
*   `lyrically.db`: The SQLite database file.
*   `proxies.txt`: An empty file where you can add your list of proxies, one per line (e.g., `http://user:pass@host:port`).

You can customize the logging verbosity by modifying the following variables in [`src/lyrically/config.py`](src/lyrically/config.py ):
*   `FILE_LOG_LEVEL`: Sets the logging level for the `Lyrically.log` file (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").
*   `CONSOLE_LOG_LEVEL`: Sets the logging level for the console output (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").


## Dependencies

Key dependencies include:
*   `aiohttp`: For asynchronous HTTP requests.
*   `beautifulsoup4`: For HTML parsing.
*   `lxml`: Efficient HTML parser backend.
*   `aiosqlite`: Asynchronous SQLite database driver.

See `setup.py` for the full list.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.