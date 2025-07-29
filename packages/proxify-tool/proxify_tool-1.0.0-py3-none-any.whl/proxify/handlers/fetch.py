import logging
import asyncio

import aiohttp

from .storage import StorageHandler
from ..config import HEADERS
from ..sources import proxyscrape, geonode, free_proxy_list, open_proxy_list, proxy_list

logger = logging.getLogger(__name__)


class FetchHandler:
    """Handles proxy fetching operations."""

    def __init__(self, storage_manager: StorageHandler) -> None:
        """
        Initialize the fetch handler instance.

        Args:
            storage_manager (StorageHandler): A handler for storage operations.
        """
        self.storage_manager = storage_manager

        logger.debug("Fetch handler has been initialized.")

    async def get_proxies(self) -> None:
        """Fetch and store proxies from various sources."""
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            tasks = [
                proxyscrape.get(session, self.storage_manager),
                geonode.get(session, self.storage_manager),
                free_proxy_list.get(session, self.storage_manager),
                open_proxy_list.get(session, self.storage_manager),
                proxy_list.get(session, self.storage_manager),
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
