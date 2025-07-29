import logging
import asyncio
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
    Fetch and store proxies from a specific OpenProxyList URL.

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
            proxy_urls = set(
                f"{proxy_type}://{proxy}" for proxy in response.splitlines() if proxy
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
    Fetch and store proxies from OpenProxyList.

    Args:
        session (aiohttp.ClientSession): The session object to make HTTP requests with.
        storage_manager (StorageHandler): A handler for storage operations.
    """
    logger.debug("Attempting to fetch proxies from %s.", method_name)

    # Create and start tasks for each URL
    urls = {
        proxy_type: f"https://raw.githubusercontent.com/roosterkid/openproxylist/refs/heads/main/{proxy_type.upper()}_RAW.txt"
        for proxy_type in ("https", "socks4", "socks5")
    }

    tasks = [
        get_url(session, storage_manager, urls[proxy_type], proxy_type)
        for proxy_type in urls
    ]
    await asyncio.gather(*tasks)

    logger.debug("Proxies from %s have been fetched.", method_name)
