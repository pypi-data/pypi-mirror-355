"""
I/O Utilities
=============

This module defines and implements Courtesy's I/O interface.

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

file_handler = FileHandler(GNARLY_LOG_DIR / "courtesy.log")
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
    # Input validation
    if not isinstance(s, str):
        raise TypeError("Input 's' must be a string")
    
    if not isinstance(cps, int) or cps <= 0:
        raise ValueError("cps must be a positive integer")
    
    if charlim is not None and (not isinstance(charlim, int) or charlim <= 0):
        raise ValueError("charlim must be a positive integer or None")
    
    # Handle empty string
    if not s:
        return None
    
    # Get terminal width with silent fallback
    try:
        term_width: int = os.get_terminal_size().columns
        charlim: int = charlim or max(20, term_width - 12)  # Ensure minimum width
    except (OSError, AttributeError):
        # Log to file only (DEBUG level), not console
        logger.debug("Failed to get terminal width, using default charlim")
        charlim: int = charlim or 80  # Standard terminal width fallback

    # Ensure charlim is reasonable
    if charlim < 10:
        charlim = 10
    elif charlim > 200:
        charlim = 200

    lines = s.splitlines()
    wsp = string.whitespace
    break_chars = ["-", "–", "—", "─"]  # Extended dash characters
    
    try:
        delay: float = 1.0 / cps
    except ZeroDivisionError as e:
        logger.error(
            "User attempted to specify a value of zero characters per second, "
            "resulting in a `ZeroDivisionError`, because function `courtesy."
            "utilities.io.stream` calculates the system sleep duration as the "
            "reciprocal of `cps`."
        )
        raise ValueError("cps cannot be zero") from e

    # Handle case where charlim is not set or is very large
    if not charlim or charlim >= max(len(line) for line in lines) if lines else True:
        for line in lines:
            for c in line: 
                print(c, end="", flush=True)
                sleep(delay)
            print()  # Simplified newline
        return None

    # Process with character limit
    for line in lines:
        if not line:  # Handle empty lines
            print()
            continue
            
        chars = list(enumerate(line))  # Convert to list to avoid iterator issues
        i = 0
        
        while i < len(chars):
            char_index, c = chars[i]
            
            # Normal character printing (not at line limit)
            if (char_index % charlim != 0) or char_index == 0:
                print(c, end="", flush=True)
                sleep(delay)
                i += 1
                
            # At character limit - check for good break point
            elif char_index % charlim == 0:
                # If current character is a good break point
                if c in wsp or c in break_chars:
                    print(c + "\n", end="", flush=True)
                    sleep(delay)
                    i += 1
                    
                # Look ahead for a good break point
                else:
                    print(c, end="", flush=True)
                    sleep(delay)
                    i += 1
                    
                    # Look for next whitespace or break character
                    lookahead_limit = min(20, len(chars) - i)  # Don't look too far ahead
                    found_break = False
                    
                    for j in range(lookahead_limit):
                        if i + j >= len(chars):
                            break
                            
                        _, next_c = chars[i + j]
                        print(next_c, end="", flush=True)
                        sleep(delay)
                        
                        if next_c in wsp or next_c in break_chars:
                            print("\n", end="", flush=True)
                            found_break = True
                            i += j + 1
                            break
                    
                    # If no break found within lookahead, force break
                    if not found_break:
                        print("\n", end="", flush=True)
                        i += lookahead_limit
                        
            else:
                # This shouldn't happen, but handle it gracefully
                logger.debug(f"Unexpected condition at index {char_index}, character '{c}'")
                print(c, end="", flush=True)
                sleep(delay)
                i += 1
                
        print()  # End of line

    return None


def div(
    printer: callable = stream,
    decoration: str = "✦",
    charlim: int | None = None
) -> None:
    """
    Print a dynamically sized divider to ``stdout``.

    Returns
    -------
    None

    """
    try:
        term_width = os.get_terminal_size().columns
        charlim = term_width - 12
    except OSError as e:
        logger.error(f"Could not get terminal size: {e}")
        charlim = 40

    divider = ("─" * (charlim-4)) + f" {decoration} ─"

    printer(divider)

