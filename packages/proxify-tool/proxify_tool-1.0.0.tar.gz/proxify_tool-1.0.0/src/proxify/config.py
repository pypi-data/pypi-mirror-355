import os
from dotenv import load_dotenv

load_dotenv()

# Storage variables
STORAGE_DIR = "storage/"

# Logging variables
CONSOLE_LOG_LEVEL, FILE_LOG_LEVEL = None, None
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

if DEBUG_MODE:
    CONSOLE_LOG_LEVEL, FILE_LOG_LEVEL = "DEBUG", "DEBUG"
else:
    CONSOLE_LOG_LEVEL, FILE_LOG_LEVEL = "INFO", "INFO"

# Network variables
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Priority": "u=0, i",
    "Sec-Ch-UA": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
    "Sec-Ch-UA-Mobile": "?0",
    "Sec-Ch-UA-Platform": '"macOS"',
    "Sec-Gpc": "1",
}
VALIDATION_CONCURRENCY_LIMIT = 1750
