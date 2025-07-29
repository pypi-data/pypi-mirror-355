import logging
import asyncio
from pathlib import Path

import aiohttp
from bs4 import BeautifulSoup

from ..handlers.storage import StorageHandler

logger = logging.getLogger(__name__)
method_name = Path(__file__).stem


async def get_url(
    session: aiohttp.ClientSession, storage_manager: StorageHandler, url: str
) -> None:
    """
    Fetch and store proxies from a specific FreeProxyList sub-site URL.

    Args:
        session (aiohttp.ClientSession): The session to send HTTP requests with.
        storage_manager (StorageHandler): A handler for storage operations.
        url (str): The URL to send a request to.
    """
    try:
        # Send HTTP request for proxies
        async with session.get(url) as response:
            response = await response.text()

        if response:
            # Parse proxies
            proxy_urls = set()

            soup = BeautifulSoup(response, "lxml")
            main_section = soup.find("section", {"id": "list"})
            main_container = main_section.find("div", class_="container")
            table_body = main_container.find("tbody")
            table_rows = table_body.find_all("tr")

            for table_row in table_rows:
                table_row_datas = table_row.find_all("td")
                proxy_ip, proxy_port, proxy_type = None, None, None

                for i, trd in enumerate(table_row_datas):
                    if i == 0:
                        proxy_ip = trd.get_text()
                    if i == 1:
                        proxy_port = trd.get_text()
                    if i == 4:
                        proxy_type = "socks4" if trd.get_text() == "Socks4" else None
                    if i == 6 and not proxy_type:
                        proxy_type = "https" if trd.get_text() == "yes" else "http"

                if proxy_type and proxy_ip and proxy_port:
                    proxy_url = f"{proxy_type}://{proxy_ip}:{proxy_port}"
                    proxy_urls.add(proxy_url)
                else:
                    logger.error(
                        "Unable to get proxy type, ip or port from %s in %s",
                        url,
                        method_name,
                    )

            # Store proxies
            for proxy_url in proxy_urls:
                await storage_manager.store_fetched_proxy(proxy_url)
        else:
            logger.error("Unable to get response from %s in %s.", url, method_name)

    except asyncio.TimeoutError:
        logger.exception(
            "Timed out while fetching proxies from %s in %s.", url, method_name
        )
    except aiohttp.ClientConnectorError:
        logger.exception(
            "Client connection error while fetching proxies from %s in %s.",
            url,
            method_name,
        )
    except aiohttp.ClientError:
        logger.exception(
            "Aiohttp client error while fetching proxies from %s in %s.",
            url,
            method_name,
        )
    except Exception:
        logger.exception(
            "General error occurred while fetching proxies from %s in %s.",
            url,
            method_name,
        )


async def get(session: aiohttp.ClientSession, storage_manager: StorageHandler) -> None:
    """
    Fetch and store proxies from FreeProxyList and its sub-sites.

    Args:
        session (aiohttp.ClientSession): The session object to make HTTP requests with.
        storage_manager (StorageHandler): A handler for storage operations.
    """
    logger.debug("Attempting to fetch proxies from %s.", method_name)

    # Create and start tasks for each URL
    urls = [
        "https://www.socks-proxy.net/",
        "https://free-proxy-list.net/",
        "https://www.us-proxy.org/",
        "https://free-proxy-list.net/uk-proxy.html",
        "https://www.sslproxies.org/",
        "https://free-proxy-list.net/anonymous-proxy.html",
    ]

    tasks = [get_url(session, storage_manager, url) for url in urls]
    await asyncio.gather(*tasks)

    logger.debug("Proxies from %s have been fetched.", method_name)
