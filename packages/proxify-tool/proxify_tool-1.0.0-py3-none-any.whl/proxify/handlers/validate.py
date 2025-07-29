import logging
import asyncio

import aiohttp
from aiohttp_socks import ProxyConnector

from ..config import VALIDATION_CONCURRENCY_LIMIT
from .storage import StorageHandler

logger = logging.getLogger(__name__)


class ValidateHandler:
    """Handles proxy validation operations."""

    def __init__(self, storage_manager: StorageHandler) -> None:
        """
        Initialize the validate handler instance.

        Args:
            storage_manager (StorageHandler): A handler for storage operations.
        """
        self.storage_manager = storage_manager
        self.semaphore = asyncio.Semaphore(VALIDATION_CONCURRENCY_LIMIT)

        logger.debug("Validate handler has been initialized.")

    async def validate_proxy(self, session):
        async with self.semaphore:
            proxy_type = session.connector._proxy_type.name.lower()
            proxy_ip, proxy_port = (
                session.connector._proxy_host,
                session.connector._proxy_port,
            )
            proxy_url = f"{proxy_type}://{proxy_ip}:{proxy_port}"

            try:
                async with session.get("https://api.ipify.org?format=json") as response:
                    data = await response.json()

                if data and "ip" in data:
                    returned_ip = data["ip"]

                    if proxy_ip == returned_ip:
                        await self.storage_manager.store_valid_proxy(proxy_url)
                        return
                    else:
                        logger.error(
                            "IP missmatch for %s. Expected %s, Received %s",
                            proxy_url,
                            proxy_ip,
                            returned_ip,
                        )
                else:
                    logger.error(
                        "No IP was returned via %s. Response: %s", proxy_url, data
                    )

            except asyncio.TimeoutError:
                logger.exception("Timed out while validating %s", proxy_url)

            except aiohttp.ClientConnectorError:
                logger.exception(
                    "Client connection error while validating %s", proxy_url
                )

            except aiohttp.ClientError:
                logger.exception("Aiohttp client error while validating %s", proxy_url)

            except Exception:
                logger.exception(
                    "General unexpected error while validating %s", proxy_url
                )

            await self.storage_manager.store_invalid_proxy(proxy_url)

    async def initiate_validation_tasks(self, proxy_type: str):
        logger.debug("Attempting to validate %s proxies.", proxy_type.upper())

        # Create sessions to send HTTP requests with
        sessions = []
        for proxy in self.storage_manager.proxies[proxy_type][0]:
            if proxy_type in {"http", "https"}:
                proxy_url = f"http://{proxy}"
                timeout_duration = 10
            else:
                proxy_url = f"{proxy_type}://{proxy}"
                timeout_duration = 15

            sessions.append(
                aiohttp.ClientSession(
                    connector=ProxyConnector.from_url(proxy_url),
                    timeout=aiohttp.ClientTimeout(timeout_duration),
                )
            )

        # Create and start tasks
        tasks = [self.validate_proxy(session) for session in sessions]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Close the sessions
        await asyncio.gather(*(session.close() for session in sessions))
        sessions.clear()

        logger.debug("%s proxies have been validated.", proxy_type.upper())

    async def validate_proxies(self) -> None:
        """Handle the proxy validation process."""
        tasks = [
            self.initiate_validation_tasks(proxy_type)
            for proxy_type in self.storage_manager.storage_paths["fetched"]
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
