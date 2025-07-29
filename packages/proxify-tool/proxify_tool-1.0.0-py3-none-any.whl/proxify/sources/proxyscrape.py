import logging
import asyncio
import traceback
from pathlib import Path

import aiohttp

from ..handlers.storage import StorageHandler

logger = logging.getLogger(__name__)
method_name = Path(__file__).stem


async def get(session: aiohttp.ClientSession, storage_manager: StorageHandler) -> None:
    """
    Fetch and store proxies from Proxyscrape.

    Args:
        session (aiohttp.ClientSession): The session object to make HTTP requests with.
        storage_manager (StorageHandler): A handler for storage operations.
    """
    logger.debug("Attempting to fetch proxies from %s.", method_name)

    try:
        # Send HTTP request for proxies
        url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json"
        async with session.get(url) as response:
            response = await response.json()

        if response:
            # Parse proxies
            proxy_urls = set()

            for proxy_data in response["proxies"]:
                proxy_url = f"{proxy_data['protocol']}://{proxy_data['ip']}:{proxy_data['port']}"
                proxy_urls.add(proxy_url)

            # Store proxies
            for proxy_url in proxy_urls:
                await storage_manager.store_fetched_proxy(proxy_url)

            logger.debug("Proxies from %s have been fetched.", method_name)
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
