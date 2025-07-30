"""
Utilities
=========

A convenient library comprising a collection of simple Python utilities.

"""
from . import code, io, llm
from .code import (
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
from .llm.interfaces import ChatGPT, Claude


__all__ = [
    # ─── package-level exports ───────────────────────────────────────────────
    "code", "llm",

    # ─── module-level exports ────────────────────────────────────────────────
    "io",

    # ─── class-level exports ─────────────────────────────────────────────────
    "ChatGPT",
    "Claude",
    "CourtesyProject",
    "CourtesyCppProject",
    "CourtesyHaskellProject",
    "CourtesyJavaScriptProject",
    "CourtesyPythonProject",
    "CourtesyRProject",
    "CourtesyRustProject",
    "CourtesySwiftProject",
    "CourtesyProjectType",
    "Project"
]
