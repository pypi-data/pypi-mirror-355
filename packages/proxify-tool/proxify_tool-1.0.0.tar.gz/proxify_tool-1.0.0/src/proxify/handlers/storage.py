import logging
import asyncio
from typing import Dict
from urllib.parse import urlparse

from ..utils.storage import StoragePaths

logger = logging.getLogger(__name__)


class StorageHandler:
    """Handles storage operations."""

    def __init__(self, storage_paths: StoragePaths) -> None:
        """
        Initialize the storage handler instance.

        Args:
            storage_paths (StoragePaths): A dictionary containing all the storage paths.
        """
        self.storage_paths = storage_paths
        self.storage_lock = asyncio.Lock()

        # A structure containing locks for each storage file.
        self.file_locks = {
            "fetched": {
                protocol: asyncio.Lock() for protocol in self.storage_paths["fetched"]
            },
            "validated": {
                protocol: {"valid": asyncio.Lock(), "invalid": asyncio.Lock()}
                for protocol in self.storage_paths["validated"]
            },
        }

        # A structure that holds our fetched and valid proxies counts
        self.proxies = {
            "http": [set(), 0],
            "https": [set(), 0],
            "socks4": [set(), 0],
            "socks5": [set(), 0],
        }

        logger.debug("Storage handler has been initialized.")

    def display_fetched_counts(self) -> None:
        """Logs the total count of proxies fetched for each type."""
        logger.info(
            "Fetched Proxies: %s HTTP, %s HTTPS, %s SOCKS4, %s SOCKS5.",
            len(self.proxies["http"][0]),
            len(self.proxies["https"][0]),
            len(self.proxies["socks4"][0]),
            len(self.proxies["socks5"][0]),
        )

    def display_validated_counts(self) -> None:
        """Logs the total count of validated proxies for each type."""
        logger.info(
            "Validated Proxies: (%s/%s) HTTP, (%s/%s) HTTPS, (%s/%s) SOCKS4, (%s/%s) SOCKS5.",
            self.proxies["http"][1],
            len(self.proxies["http"][0]),
            self.proxies["https"][1],
            len(self.proxies["https"][0]),
            self.proxies["socks4"][1],
            len(self.proxies["socks4"][0]),
            self.proxies["socks5"][1],
            len(self.proxies["socks5"][0]),
        )

    async def store_fetched_proxy(self, proxy_url: str) -> None:
        """
        Store fetched proxy into the appropriate storage file.

        Args:
            proxy_url (str): The URL of the proxy to store.
        """
        # Determine if proxy has already been stored.
        async with self.storage_lock:
            # Parse the attributes of the proxy
            parsed_proxy_url = urlparse(proxy_url)
            proxy_type, proxy_ip, proxy_port = (
                parsed_proxy_url.scheme,
                parsed_proxy_url.hostname,
                parsed_proxy_url.port,
            )
            proxy_ip_port = f"{proxy_ip}:{proxy_port}"

            if proxy_ip_port in self.proxies[proxy_type][0]:
                return

        # Store the proxy
        storage_path = self.storage_paths["fetched"][proxy_type]

        async with self.file_locks["fetched"][proxy_type]:
            try:
                with open(storage_path, "a") as f:
                    if f.tell() != 0:
                        f.write("\n")
                    f.write(proxy_ip_port)

                async with self.storage_lock:
                    self.proxies[proxy_type][0].add(proxy_ip_port)

            except PermissionError:
                logger.exception(
                    "Permission denied while writing %s into %s.",
                    proxy_ip_port,
                    storage_path,
                )
            except OSError:
                logger.exception(
                    "OS error occurred while writing %s into %s.",
                    proxy_ip_port,
                    storage_path,
                )
            except Exception as e:
                logger.exception(
                    "General error occurred while writing %s into %s.",
                    proxy_ip_port,
                    storage_path,
                )

    async def store_valid_proxy(self, proxy_url: str) -> None:
        """
        Store valid proxy into the appropriate storage file.

        Args:
            proxy_url (str): The URL of the proxy to store.
        """
        # Parse the attributes of the proxy
        parsed_proxy_url = urlparse(proxy_url)
        proxy_type, proxy_ip, proxy_port = (
            parsed_proxy_url.scheme,
            parsed_proxy_url.hostname,
            parsed_proxy_url.port,
        )
        proxy_ip_port = f"{proxy_ip}:{proxy_port}"

        # Store the proxy
        storage_path = self.storage_paths["validated"][proxy_type]["valid"]

        async with self.file_locks["validated"][proxy_type]["valid"]:
            try:
                with open(storage_path, "a") as f:
                    if f.tell() != 0:
                        f.write("\n")
                    f.write(proxy_ip_port)

                async with self.storage_lock:
                    self.proxies[proxy_type][1] += 1

            except PermissionError:
                logger.exception(
                    "Permission denied while writing %s into %s.",
                    proxy_ip_port,
                    storage_path,
                )
            except OSError:
                logger.exception(
                    "OS error occurred while writing %s into %s.",
                    proxy_ip_port,
                    storage_path,
                )
            except Exception as e:
                logger.exception(
                    "General error occurred while writing %s into %s.",
                    proxy_ip_port,
                    storage_path,
                )

    async def store_invalid_proxy(self, proxy_url: str) -> None:
        """
        Store invalid proxy into the appropriate storage file.

        Args:
            proxy_url (str): The URL of the proxy to store.
        """
        # Parse the attributes of the proxy
        parsed_proxy_url = urlparse(proxy_url)
        proxy_type, proxy_ip, proxy_port = (
            parsed_proxy_url.scheme,
            parsed_proxy_url.hostname,
            parsed_proxy_url.port,
        )
        proxy_ip_port = f"{proxy_ip}:{proxy_port}"

        # Store the proxy
        storage_path = self.storage_paths["validated"][proxy_type]["invalid"]

        async with self.file_locks["validated"][proxy_type]["invalid"]:
            try:
                with open(storage_path, "a") as f:
                    if f.tell() != 0:
                        f.write("\n")
                    f.write(proxy_ip_port)

            except PermissionError:
                logger.exception(
                    "Permission denied while writing %s into %s.",
                    proxy_ip_port,
                    storage_path,
                )
            except OSError:
                logger.exception(
                    "OS error occurred while writing %s into %s.",
                    proxy_ip_port,
                    storage_path,
                )
            except Exception as e:
                logger.exception(
                    "General error occurred while writing %s into %s.",
                    proxy_ip_port,
                    storage_path,
                )
