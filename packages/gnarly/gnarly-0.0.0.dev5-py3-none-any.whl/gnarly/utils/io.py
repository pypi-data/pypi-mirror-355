"""
I/O Utilities
=============

This module defines and implements Gnarly's I/O interface.

"""
import os
import string
import sys
from logging import (
    DEBUG, INFO, FileHandler, Formatter, StreamHandler, getLogger
)
from time import sleep

from ..constants import GNARLY_LOG_DIR

# ─── set up logging ───────────────────────────────────────────────────── ✦✦ ─
formatter: Formatter = Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = getLogger(__name__)

file_handler = FileHandler(GNARLY_LOG_DIR / "gnarly.log")
file_handler.setFormatter(formatter)
file_handler.setLevel(DEBUG)

console_handler = StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(level=INFO)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


# ─── functions ────────────────────────────────────────────────────────── ✦✦ ─
def stream(
    s: str,
    cps: int = 700,
    charlim: int | None = None
) -> Exception | None:
    """Print `s` to `stdout` at `cps` characters per second.

    Iterate over a given string-like object, printing it character-by-
    character and sleeping for a duration of 1/`cps` seconds. Optionally
    limit each line to a length of `charlim`.

    Arguments
    ---------
    s: str
    cps: int
    charlim: int, optional

    Returns
    -------
    Nothing.
    """
    try:
        term_width: int = os.get_terminal_size().columns
        charlim: int = charlim or term_width - 12
    except OSError as e:
        logger.error(f"Failed to get terminal width: {e}")
        charlim: int = charlim or 40

    lines = s.splitlines()
    wsp = string.whitespace
    counter: int = 0

    try:
        delay: int | float = 1 / cps
    except ZeroDivisionError as e:
        logger.error(
            "User attempted to specify a value of zero characters per second, "
            "resulting in a `ZeroDivisionError`, because function `gnarly."
            "utilities.io.stream` calculates the system sleep duration as the "
            "reciprocal of `cps`."
        )
        raise UserWarning from e

    if not charlim:
        for line in lines:
            for c in line: 
                print(c, end="", flush=True)
                sleep(delay)
            print("\n", end="", flush=True)
    else:
        for line in lines:
            chars = enumerate(line)
            for i, c in chars:
                if (i % charlim != 0) or i == 0:
                    print(c, end="", flush=True)
                    sleep(delay)
                elif (i % charlim) == 0 and (str(c) in wsp or str(c) in ["-", "–", "─"]):
                    print(c + "\n", end="", flush=True)
                    sleep(delay)
                elif (i % charlim == 0) and (str(c) not in wsp):
                    print(c, end="", flush=True)
                    try:
                        while True:
                            _, next_c = next(chars)
                            if str(next_c) in wsp or str(next_c) in ["-", "–", "─"]:
                                print(next_c + "\n", end="", flush=True)
                                break
                            else:
                                print(next_c, end="", flush=True)
                    except StopIteration:
                        logger.info(
                            f"Reached end of line after {counter} iterations."
                        )
                        break

                else:
                    logger.warning(
                        f"Unexpected conditions encountered:\n"
                        f"Iterating over: {str(chars)}\n"
                        f"Current index: {i} \n"
                        f"Character at current index: {c}\n"
                        f"Character limit: {charlim}\n"

                        f"\n{i} % {charlim} = {i % charlim}"
                    )
                    counter +=1
            print()

