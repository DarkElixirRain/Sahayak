"""Application logging.

Privacy is the default: never log transcripts, audio, OTPs, passwords,
PINs, financial credentials, API keys, or database credentials through
these loggers.
"""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure root logging with a consistent console format."""
    root = logging.getLogger()
    root.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    if root.handlers:
        root.handlers.clear()
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a logger for a module (use ``__name__``)."""
    return logging.getLogger(name)