import logging
import asyncio
import json
from pathlib import Path

import aiohttp

from ..handlers.storage import StorageHandler

logger = logging.getLogger(__name__)
method_name = Path(__file__).stem


async def get_url(
    session: aiohttp.ClientSession,
    storage_manager: StorageHandler,
    url: str,
    proxy_type: str,
) -> None:
    """
    Fetch and store proxies from a specific proxy-list URL.

    Args:
        session (aiohttp.ClientSession): The session to send HTTP requests with.
        storage_manager (StorageHandler): A handler for storage operations.
        url (str): The URL to send a request to.
        proxy_type (str): The type of proxies to request for.
    """
    try:
        # Send HTTP request for proxies
        async with session.get(url) as response:
            response = await response.text()

        if response:
            # Parse proxies
            proxy_urls = set()
            data = json.loads(response)

            for proxy_data in data["LISTA"]:
                proxy_ip = proxy_data["IP"]
                proxy_port = proxy_data["PORT"]

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


async def get(session: aiohttp.ClientSession, storage_manager: StorageHandler) -> None:
    """
    Fetch and store proxies from Proxy-List.

    Args:
        session (aiohttp.ClientSession): The session object to make HTTP requests with.
        storage_manager (StorageHandler): A handler for storage operations.
    """
    logger.debug("Attempting to fetch proxies from %s.", method_name)

    # Create and start tasks for each URL
    urls = {
        proxy_type: f"https://www.proxy-list.download/api/v2/get?l=en&t={proxy_type}"
        for proxy_type in ("http", "https", "socks4", "socks5")
    }

    tasks = [
        get_url(session, storage_manager, urls[proxy_type], proxy_type)
        for proxy_type in urls
    ]
    await asyncio.gather(*tasks)

    logger.debug("Proxies from %s have been fetched.", method_name)
