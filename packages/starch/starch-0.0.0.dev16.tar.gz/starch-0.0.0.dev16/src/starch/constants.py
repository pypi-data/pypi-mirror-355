"""Constants

This module contains constants used throughout the Starch code package.
"""
# ─── import statements ────────────────────────────────────────────────── ✦✦ ──
# standard library imports

from pathlib import Path
from typing import Final

# third-party imports
from platformdirs import (
    user_cache_path, user_config_path, user_data_path, user_log_path
)

    
# ─── constants ────────────────────────────────────────────────────────── ✦✦ ──
__author__: Final[str] = "k.lebryce"
__version__: Final[str] = "0.0.0"
__package__: Final[str] = "starch"

STARCH_CACHE_DIR: Final[Path] = user_cache_path(
    __package__.capitalize(), __author__, ensure_exists=True
)

STARCH_CONFIG_DIR: Final[Path] = user_config_path(
    __package__.capitalize(), __author__, ensure_exists=True
)

STARCH_DATA_DIR: Final[Path] = user_data_path(
    __package__.capitalize(), __author__, ensure_exists=True
)

STARCH_LOG_DIR: Final[Path] = user_log_path(
    __package__.capitalize(), __author__, ensure_exists=True
)

STARCH_CONFIG_FILEPATH: Final[Path] = STARCH_CONFIG_DIR / "config.json"
STARCH_LOG_FILEPATH: Final[Path] = STARCH_LOG_DIR / f"{__package__}.log"
