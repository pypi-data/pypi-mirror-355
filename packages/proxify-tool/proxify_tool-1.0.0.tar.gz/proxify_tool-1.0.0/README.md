# Proxify

Proxify is a Python tool for fetching and validating public proxies from various online sources.

## Features

*   **Multi-Source Proxy Fetching:** Retrieves proxies from several providers:
    *   Proxyscrape
    *   Geonode
    *   FreeProxyList
    *   OpenProxyList
    *   Proxy-List.download
*   **Proxy Validation:** Checks the status of fetched proxies.
*   **Local Storage:** Saves fetched and validated proxies into organized text files.
*   **Asynchronous Operations:** Utilizes `asyncio` and `aiohttp` for non-blocking network requests.
*   **Configurable Logging:** Provides detailed logging for both console and file outputs, with configurable levels.
*   **HTML Parsing:** Uses `BeautifulSoup` with `lxml` for robust parsing of web pages from certain sources.
*   **User-Agent Customization:** Uses configurable HTTP headers for requests.

## Installation

You can install `proxify` directly from GitHub or by cloning the repository.

### From GitHub Releases (Recommended when available)

1.  Go to the [Releases page](https://github.com/filming/proxify/releases) (replace with your actual repository URL).
2.  Download the latest `.whl` file.
3.  Install it using pip:
    ```bash
    pip install /path/to/downloaded/proxify-X.Y.Z-py3-none-any.whl
    ```
    Replace `X.Y.Z` with the actual version number and `/path/to/downloaded/` with the correct path to the file.

### From Source (after cloning)

1.  Clone the repository:
    ```bash
    git clone https://github.com/filming/proxify.git # Replace with your actual repository URL
    cd proxify
    ```
2.  Install using pip (this will also install dependencies listed in [`pyproject.toml`](pyproject.toml)):
    ```bash
    pip install .
    ```
    If you are developing the project, you might prefer an editable install:
    ```bash
    pip install -e .
    ```

## Usage

Here's a basic example of how to use Proxify:

```python
import asyncio
from proxify import Proxify

async def main():
    # Initialize Proxify
    proxify = Proxify()

    try:
        # Fetch proxies from all configured sources
        await proxify.get_proxies()
        print("Proxy fetching complete.")

        # Validate the fetched proxies
        await proxify.validate_proxies()
        print("Proxy validation complete.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

Proxify handles its configuration and storage as follows:

*   **Storage Directory:** Upon first run, Proxify creates a `storage/` directory in the project root (this path is defined by `STORAGE_DIR` in [`src/proxify/config.py`](src/proxify/config.py)). This directory contains:
    *   `logs/Proxify.log`: The application log file, configured by [`src/proxify/utils/logger.py`](src/proxify/utils/logger.py).
    *   `proxies/fetched/`: Contains text files (`http.txt`, `https.txt`, `socks4.txt`, `socks5.txt`) with all proxies fetched from sources.
    *   `proxies/validated/`: Contains subdirectories for each protocol (`http/`, `https/`, `socks4/`, `socks5/`). Each subdirectory has:
        *   `valid.txt`: List of proxies that passed validation.
        *   `invalid.txt`: List of proxies that failed validation.

*   **Logging:**
    *   Log levels can be controlled by setting the `DEBUG_MODE` environment variable. If `DEBUG_MODE` is set to `"true"`, both console and file log levels are set to `DEBUG`. Otherwise, they default to `INFO`.
    *   You can also directly modify `CONSOLE_LOG_LEVEL` and `FILE_LOG_LEVEL` in [`src/proxify/config.py`](src/proxify/config.py).

*   **HTTP Headers:** Default HTTP headers for requests are defined in `HEADERS` within [`src/proxify/config.py`](src/proxify/config.py).
*   **Validation Concurrency:** The concurrency limit for proxy validation can be adjusted via `VALIDATION_CONCURRENCY_LIMIT` in [`src/proxify/config.py`](src/proxify/config.py).

## Dependencies

Key dependencies are managed by `setuptools` via [`pyproject.toml`](pyproject.toml) and include:
*   `aiohttp`: For asynchronous HTTP clients.
*   `aiohttp-socks`: For SOCKS proxy support with aiohttp.
*   `beautifulsoup4`: For parsing HTML and XML.
*   `python-dotenv`: For loading environment variables from a `.env` file.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.