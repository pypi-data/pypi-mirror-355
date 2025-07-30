"""
Utilities
=========

A convenient library comprising a collection of simple Python utilities.

"""
from . import code, io, llm
from .code import (
    GnarlyProject,
    GnarlyCppProject,
    GnarlyHaskellProject,
    GnarlyJavaScriptProject,
    GnarlyPythonProject,
    GnarlyRProject,
    GnarlyRustProject,
    GnarlySwiftProject,
    GnarlyProjectType,
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
    "GnarlyProject",
    "GnarlyCppProject",
    "GnarlyHaskellProject",
    "GnarlyJavaScriptProject",
    "GnarlyPythonProject",
    "GnarlyRProject",
    "GnarlyRustProject",
    "GnarlySwiftProject",
    "GnarlyProjectType",
    "Project"
]
