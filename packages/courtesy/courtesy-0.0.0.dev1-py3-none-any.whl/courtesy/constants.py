"""Constants

This module defines the constant values referenced throughout the `courtesy`
code base.

"""

import logging
from pathlib import Path

from dotenv import load_dotenv
from platformdirs import (
    user_cache_path,
    user_config_path,
    user_data_path,
    user_log_path
)

# ─── logger setup ─────────────────────────────────────────────────────── ✦✦ ─
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# ─── package metadata ─────────────────────────────────────────────────── ✦✦ ─
__author__: str = "K. LeBryce <kosmolebryce@gmail.com>"
__package__: str = "Courtesy"
__version__: str = "0.0.0"
__description__: str = "A sophisticated abstraction layer for lazy developers."

# ─── resource references ──────────────────────────────────────────────── ✦✦ ─
GNARLY_DATA_DIR: Path = user_data_path(
    __package__,
    __author__,
    __version__,
    ensure_exists=True
)

GNARLY_CACHE_DIR: Path = user_cache_path(
    __package__,
    __author__,
    __version__,
    ensure_exists=True
)

GNARLY_CONFIG_DIR: Path = user_config_path(
    __package__,
    __author__,
    __version__,
    ensure_exists=True
)

GNARLY_LOG_DIR: Path = user_log_path(
    __package__,
    __author__,
    __version__,
    ensure_exists=True
)

GNARLY_PROJECT_ROOT_PATH: Path = Path.home() / "courtesy/"
GNARLY_PROJECT_ROOT_PATH.mkdir(exist_ok=True)

DOTENV_FILE_PATH: Path = GNARLY_CONFIG_DIR / "courtesy.env"
DOTENV_FILE_PATH.touch()

try:
    logger.info(
        f"Loading environment variables from {DOTENV_FILE_PATH.resolve()}"
    )
    load_dotenv(DOTENV_FILE_PATH)
    logging.info("Successfully loaded environment variables.")
except FileNotFoundError as e:
    logger.error(
        f"Could not find `courtesy.env` in {GNARLY_CONFIG_DIR.resolve()}"
    )
    raise RuntimeError from e
except IOError as e:
    logger.error(
        f"Encountered an unspecified I/O error while attempting to read from "
        f"{GNARLY_CONFIG_DIR.resolve()}"
    )
    raise RuntimeError from e

