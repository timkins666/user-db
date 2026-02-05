"""Centralised logger setup."""

import logging
import os


def get_logger(name: str):
    """
    Returns a named logger, set to `$LOG_LEVEL` or INFO default
    """

    logger = logging.getLogger(name)
    # determine level from env, default to INFO
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)

    # If no handlers are attached, add a StreamHandler so output appears on stdout
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Avoid double logging if root logger also configured
    logger.propagate = False

    return logger
