import logging

from .utils.logger import setup_logging
from .utils.storage import create_storage_locations
from .handlers.fetch import FetchHandler
from .handlers.storage import StorageHandler
from .handlers.validate import ValidateHandler

logger = logging.getLogger(__name__)


class Proxify:
    """Handles the fetching and validation of public proxies."""

    def __init__(self) -> None:
        """Initialize the proxify instance."""
        setup_logging()

        storage_paths = create_storage_locations()
        self.storage_manager = StorageHandler(storage_paths)
        self.fetcher = FetchHandler(self.storage_manager)
        self.validator = ValidateHandler(self.storage_manager)

        logging.info("Proxify instance has been initialized.")

    async def get_proxies(self) -> None:
        """Fetch and store proxies from various sources."""
        logger.info("Fetching proxies from various sources.")
        await self.fetcher.get_proxies()
        logger.info("Fetched proxies from various sources.")

        self.storage_manager.display_fetched_counts()

    async def validate_proxies(self):
        """Validate the fetched proxies from various sources."""
        logger.info("Validating fetched proxies.")
        await self.validator.validate_proxies()
        logger.info("Validated fetched proxies.")

        self.storage_manager.display_validated_counts()
