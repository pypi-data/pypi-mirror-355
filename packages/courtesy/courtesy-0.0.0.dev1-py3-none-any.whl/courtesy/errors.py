"""
Errors
======

This module defines the custom exception types used throughout the
code base. This is a Courtesy implementation detail.
"""

import logging

from .constants import GNARLY_LOG_DIR

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    filename=(GNARLY_LOG_DIR / "courtesy.log").resolve()
)
logger.info("Logger setup complete.")

class CourtesyError(Exception):
    """Courtesy's base error class."""
    pass


class NamespaceError(CourtesyError):
    """
    An error type that arises from an improper namespace access attempt.
    """
    pass
