import logging
import math
import asyncio
from pathlib import Path

import aiohttp

from ..handlers.storage import StorageHandler

logger = logging.getLogger(__name__)
method_name = Path(__file__).stem


async def get_url(
    session: aiohttp.ClientSession, storage_manager: StorageHandler, url: str
) -> None:
    """
    Fetch and store proxies from a specific geonode URL.

    Args:
        session (aiohttp.ClientSession): The session to send HTTP requests with.
        storage_manager (StorageHandler): A handler for storage operations.
        url (str): The URL to send a request to.
    """
    try:
        # Send HTTP request for proxies
        async with session.get(url) as response:
            response = await response.json()

        if response:
            # Parse proxies
            proxy_urls = set()

            if response["data"]:
                for proxy_data in response["data"]:
                    proxy_type = proxy_data["protocols"][0]
                    proxy_ip = proxy_data["ip"]
                    proxy_port = proxy_data["port"]

                    proxy_url = f"{proxy_type}://{proxy_ip}:{proxy_port}"
                    proxy_urls.add(proxy_url)

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


async def get_url_count(session: aiohttp.ClientSession) -> int | None:
    """
    Determine the number of URLs required to fetch all available proxies.

    Args:
        session (aiohttp.ClientSession): The session to send HTTP requests with.

    Returns:
        int | None: The number of URLs needed to fetch all available proxies,
                    or None if the count could not be determined.
    """
    try:
        url = "https://proxylist.geonode.com/api/proxy-list?limit=1&page=1"
        async with session.get(url) as response:
            response = await response.json()

        if response:
            total_proxies = response["total"]
            url_count = math.ceil(total_proxies / 500)

            return url_count
        else:
            logger.error("Unable to get response from %s in %s.", url, method_name)

    except asyncio.TimeoutError:
        logger.exception(
            "Timed out while getting url count from %s in %s.", url, method_name
        )
    except aiohttp.ClientConnectorError:
        logger.exception(
            "Client connection error while getting url count from %s in %s.",
            url,
            method_name,
        )
    except aiohttp.ClientError:
        logger.exception(
            "Aiohttp client error while getting url count from %s in %s.",
            url,
            method_name,
        )
    except Exception:
        logger.exception(
            "General error occurred while getting url count from %s in %s.",
            url,
            method_name,
        )


async def get(session: aiohttp.ClientSession, storage_manager: StorageHandler) -> None:
    """
    Fetch and store proxies from Geonode.

    Args:
        session (aiohttp.ClientSession): The session object to make HTTP requests with.
        storage_manager (StorageHandler): A handler for storage operations.
    """
    logger.debug("Attempting to fetch proxies from %s.", method_name)

    url_count = await get_url_count(session)

    if url_count:
        urls = [
            f"https://proxylist.geonode.com/api/proxy-list?limit=500&page={i}"
            for i in range(1, url_count + 1)
        ]

        # Create and start tasks for each URL
        tasks = [get_url(session, storage_manager, url) for url in urls]
        await asyncio.gather(*tasks)

        logger.debug("Proxies from %s have been fetched.", method_name)
    else:
        logger.error("Unable to find number of URLs required from %s.", method_name)
