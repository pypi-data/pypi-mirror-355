"""
Gnarly
======

A general-use abstraction layer for the lazy.

"""
import logging

from . import constants, utilities
from .utilities import io, stream

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    import starch
    __all__ = ["starch"]
except ImportError as e:
    logger.error(f"Could not import `starch`: {e}")

__all__ = [
    # ─── package-level exports ───────────────────────────────────────────────
    "utilities",

    # ─── module-level exports ────────────────────────────────────────────────
    "constants", "io",

    # ─── function-level exports ──────────────────────────────────────────────
    "stream"
]
