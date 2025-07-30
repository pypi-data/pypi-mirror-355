"""
Courtesy
======

A general-use abstraction layer for the lazy.

"""
import logging

from . import errors, constants, utils
from .errors import NamespaceError
from .utils import code, io, llm
from .utils.code.projects import (
    CourtesyProject,
    CourtesyCppProject,
    CourtesyHaskellProject,
    CourtesyJavaScriptProject,
    CourtesyPythonProject,
    CourtesyRProject,
    CourtesyRustProject,
    CourtesySwiftProject,
    CourtesyProjectType,
    Project
)
from .utils.io import div, stream
from .utils.llm import claude, chatgpt, ChatGPT, Claude

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    import starch
    __all__ = ["starch"]
except ImportError as e:
    logger.error(f"Could not import `starch`: {e}")

__all__ = [
    # ─── package-level exports ───────────────────────────────────────────────
    "code", "llm", "utils",

    # ─── module-level exports ────────────────────────────────────────────────
    "chatgpt", "claude", "errors", "constants", "io",

    # ─── function-level exports ──────────────────────────────────────────────
    "div", "stream",

    # ─── class-level exports ─────────────────────────────────────────────────
    "ChatGPT", "Claude",
    "CourtesyProject", "CourtesyCppProject", "CourtesyHaskellProject",
    "CourtesyJavaScriptProject", "CourtesyPythonProject", "CourtesyRustProject",
    "CourtesyRProject", "CourtesyRustProject", "CourtesySwiftProject",
    "CourtesyProjectType", "NamespaceError", "Project"
]
