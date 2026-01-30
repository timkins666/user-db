import logging
import os


def get_logger(name: str):
    """
    Returns a named logger, set to `$LOG_LEVEL` or INFO default
    """

    logger = logging.getLogger(name)
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    return logger
