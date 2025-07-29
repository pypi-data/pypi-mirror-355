import logging
from pathlib import Path
from typing import TypedDict

from ..config import STORAGE_DIR

logger = logging.getLogger(__name__)


# TypedDict classes make function type-hinting clearer
class FetchedPaths(TypedDict):
    http: Path
    https: Path
    socks4: Path
    socks5: Path


class ValidatedProtocolPaths(TypedDict):
    invalid: Path
    valid: Path


class ValidatedPaths(TypedDict):
    http: ValidatedProtocolPaths
    https: ValidatedProtocolPaths
    socks4: ValidatedProtocolPaths
    socks5: ValidatedProtocolPaths


class StoragePaths(TypedDict):
    Fetched: FetchedPaths
    validated: ValidatedPaths


def create_storage_locations() -> StoragePaths:
    """
    Create storage directories and paths.

    Returns:
        StoragePaths: A dictionary containing all the proxy paths.
    """
    logger.debug("Attempting to create storage locations.")

    storage_dir = Path(STORAGE_DIR)

    # Define base directories
    fetched_proxies_dir = storage_dir / "proxies" / "fetched"
    validated_proxies_dir = storage_dir / "proxies" / "validated"

    validated_http_proxies_dir = validated_proxies_dir / "http"
    validated_https_proxies_dir = validated_proxies_dir / "https"
    validated_socks4_proxies_dir = validated_proxies_dir / "socks4"
    validated_socks5_proxies_dir = validated_proxies_dir / "socks5"

    # Create directories if they don't exist
    dirs_to_create = [
        fetched_proxies_dir,
        validated_http_proxies_dir,
        validated_https_proxies_dir,
        validated_socks4_proxies_dir,
        validated_socks5_proxies_dir,
    ]

    for dir_path in dirs_to_create:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {dir_path}")
        except OSError as e:
            msg = f"Error creating directory {dir_path}"
            logger.exception(msg)
            raise OSError(msg) from e

    paths = {
        "fetched": {
            "http": fetched_proxies_dir / "http.txt",
            "https": fetched_proxies_dir / "https.txt",
            "socks4": fetched_proxies_dir / "socks4.txt",
            "socks5": fetched_proxies_dir / "socks5.txt",
        },
        "validated": {
            "http": {
                "invalid": validated_http_proxies_dir / "invalid.txt",
                "valid": validated_http_proxies_dir / "valid.txt",
            },
            "https": {
                "invalid": validated_https_proxies_dir / "invalid.txt",
                "valid": validated_https_proxies_dir / "valid.txt",
            },
            "socks4": {
                "invalid": validated_socks4_proxies_dir / "invalid.txt",
                "valid": validated_socks4_proxies_dir / "valid.txt",
            },
            "socks5": {
                "invalid": validated_socks5_proxies_dir / "invalid.txt",
                "valid": validated_socks5_proxies_dir / "valid.txt",
            },
        },
    }

    logger.info("Storage locations initialized.")
    return paths
