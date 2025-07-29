"""
Logging module that prepares a custom logger. Overrides logging built-in package
"""
import logging
from logging import Logger

from rich.logging import RichHandler

# formatter = logging.Formatter("%(levelname)s | %(funcName)s | %(message)s")

logger = logging.getLogger("bw2scaffold")
logger.handlers = []
handler = RichHandler(show_path=False, markup=True)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def getLogger(name: str, debug: bool = False) -> Logger:
    logger = logging.getLogger(name)

    if debug:
        logger.setLevel(logging.DEBUG)
        logger.handlers = []
        handler = RichHandler(
            show_path=True,
            omit_repeated_times=False,
            markup=True,
            rich_tracebacks=True,
        )
        logger.addHandler(handler)
    return logger
