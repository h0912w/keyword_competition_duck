"""signal_handler module for KCPC.

Handles Ctrl+C safe shutdown.
"""

import signal
import sys
from threading import Event

from kcpc.logging_config import get_logger

logger = get_logger()

# Global shutdown event
_shutdown_event = Event()


def get_shutdown_event() -> Event:
    """Get the global shutdown event.

    Returns:
        Event: Threading event that is set when shutdown is requested.
    """
    return _shutdown_event


def setup_signal_handlers() -> None:
    """Setup signal handlers for graceful shutdown."""
    # Handle Ctrl+C (SIGINT)
    signal.signal(signal.SIGINT, _handle_signal)

    # Handle termination signal (SIGTERM) on Unix
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_signal)

    logger.debug("Signal handlers registered")


def _handle_signal(signum: int, frame) -> None:  # type: ignore
    """Handle shutdown signals.

    Args:
        signum: Signal number.
        frame: Current stack frame.
    """
    signal_name = signal.Signals(signum).name if hasattr(signal, "Signals") else str(signum)
    logger.info(f"Received {signal_name}, initiating graceful shutdown...")

    # Set shutdown event
    _shutdown_event.set()

    # Note: We don't call sys.exit() here to allow the pipeline
    # to complete the current keyword and save state


def is_shutdown_requested() -> bool:
    """Check if shutdown has been requested.

    Returns:
        bool: True if shutdown was requested via Ctrl+C or signal.
    """
    return _shutdown_event.is_set()
