import logging
import sys
from pathlib import Path

from ..config import STORAGE_DIR, CONSOLE_LOG_LEVEL, FILE_LOG_LEVEL


def setup_logging() -> None:
    """Configure root logger."""
    # Determine directory locations
    storage_dir = Path(STORAGE_DIR)

    logs_dir = storage_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "Proxify.log"

    # Determine log levels
    log_values = {10: "DEBUG", 20: "INFO", 30: "WARN", 40: "ERROR", 50: "CRITICAL"}

    file_log_level = getattr(logging, FILE_LOG_LEVEL.upper(), logging.INFO)
    console_log_level = getattr(logging, CONSOLE_LOG_LEVEL.upper(), logging.INFO)

    # Set formatter for file and console handlers
    formatter = logging.Formatter(
        "[%(asctime)s] %(name)-35s %(levelname)-8s [%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure file and console handlers
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(file_log_level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_log_level)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Control third-party log levels
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    root_logger.info(
        "Logging configured. File level: %s, Console level: %s",
        log_values[file_log_level],
        log_values[console_log_level],
    )
