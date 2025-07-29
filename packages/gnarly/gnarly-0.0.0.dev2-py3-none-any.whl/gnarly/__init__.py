"""
Gnarly
======

A general-use abstraction layer for the lazy.

"""

from . import constants, utilities
from .utilities import io, stream


__all__ = [
    # ─── package-level exports ───────────────────────────────────────────────
    "utilities",

    # ─── module-level exports ────────────────────────────────────────────────
    "constants", "io",

    # ─── function-level exports ──────────────────────────────────────────────
    "stream"
]
