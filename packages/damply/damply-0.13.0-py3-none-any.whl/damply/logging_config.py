import os
import sys
from loguru import logger

# Read environment variable or default to WARNING
log_level = os.getenv("DAMPLY_LOG_LEVEL", "WARNING").upper()

# change the log level of the logger
logger.remove()  # Remove the default logger
logger.add(
    sys.stderr,
    level=log_level,
    format="<green>{time:YYYY-MM-DD}</green> | <level>{level}</level> | {message}",
    colorize=True,
)