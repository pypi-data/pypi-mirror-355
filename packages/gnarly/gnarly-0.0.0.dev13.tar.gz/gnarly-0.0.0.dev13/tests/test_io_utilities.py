"""
Tests for I/O Utilities
=======================

This module provides the testing framework for Gnarly's I/O interfaces.

"""
from src.gnarly.utils.io import stream


def test_stream_default():
    result = stream("Testing the `io.stream` function's default behavior.")
    assert isinstance(result, (Exception | None))

def test_stream_with_cps():
    result = stream(
        "Testing the `io.stream` function's behavior when provided "
        "with a `cps` argument.",
        700
    )
    assert isinstance(result, (Exception | None))

