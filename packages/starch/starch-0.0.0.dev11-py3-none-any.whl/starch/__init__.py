"""Initialization

This module exposes Starch's public API.
"""
from . import config, constants, formatter
from .constants import (
    __author__, __version__, __package__,
    STARCH_CACHE_DIR, STARCH_CONFIG_DIR, STARCH_DATA_DIR, STARCH_LOG_DIR, STARCH_LOG_FILEPATH
)

from .formatter import CommentFormatter
from .config import Configuration

__all__ = [
    "__author__", "__version__", "__package__",
    "STARCH_CACHE_DIR", "STARCH_CONFIG_DIR", "STARCH_DATA_DIR", "STARCH_LOG_DIR", "STARCH_LOG_FILEPATH",

    "CommentFormatter", "Configuration",

    "config", "constants", "formatter"
]
