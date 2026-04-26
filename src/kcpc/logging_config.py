"""logging_config module for KCPC.

Configures logging format and handlers.
"""

import logging
import sys
from pathlib import Path

from kcpc.config import get_config


def setup_logging() -> logging.Logger:
    """Configure logging for KCPC application.

    Returns:
        logging.Logger: Configured logger instance.
    """
    config = get_config()
    logger = logging.getLogger("kcpc")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Create formatters
    detailed_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)-8s] [%(name)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = logging.Formatter(
        "[%(levelname)-8s] - %(message)s"
    )

    # File handler (all levels)
    log_path = Path(config.log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Set UTF-8 encoding for console output (Windows)
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger() -> logging.Logger:
    """Get the KCPC logger instance.

    Returns:
        logging.Logger: Logger instance.
    """
    logger = logging.getLogger("kcpc")
    if not logger.handlers:
        return setup_logging()
    return logger
