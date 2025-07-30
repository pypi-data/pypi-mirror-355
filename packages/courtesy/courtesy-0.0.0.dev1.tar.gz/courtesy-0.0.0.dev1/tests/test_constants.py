"""
Constants Tests

This module comprises the entry point for the `courtesy` package's
testing suite.
"""
from src.courtesy.constants import (
    GNARLY_CACHE_DIR,
    GNARLY_CONFIG_DIR,
    GNARLY_DATA_DIR,
    GNARLY_LOG_DIR
)


# ─── resource directory validation ────────────────────────────────────── ✦✦ ─
def test_cache_dir():
    assert GNARLY_CACHE_DIR.exists()

def test_config_dir():
    assert GNARLY_CONFIG_DIR.exists()

def test_data_dir():
    assert GNARLY_DATA_DIR.exists()

def test_log_dir():
    assert GNARLY_LOG_DIR.exists()

