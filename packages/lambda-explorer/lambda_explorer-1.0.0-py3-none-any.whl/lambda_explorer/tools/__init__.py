# !/usr/bin/env python
"""Title.

Description
"""
# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------

from __future__ import annotations

import typing as tp

import coloredlogs
import verboselogs

# -----------------------------------------------------------------------------
# COPYRIGHT
# -----------------------------------------------------------------------------

__author__ = "Noel Ernsting Luz"
__copyright__ = "Copyright (C) 2022 Noel Ernsting Luz"
__license__ = "Public Domain"
__version__ = "1.0"

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# LOGGER
# -----------------------------------------------------------------------------

verboselogs.install()
logger = verboselogs.VerboseLogger("module_logger")

from functools import wraps


def log_calls(func: tp.Callable) -> tp.Callable:
    """Decorator logging function entry at verbose level."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.verbose("Calling %s", func.__qualname__)
        return func(*args, **kwargs)

    return wrapper


@log_calls
def setup_logging(level: str = "DEBUG") -> None:
    """Configure logging for this subpackage."""

    coloredlogs.install(level=level, logger=logger)
    logger.setLevel(level)


setup_logging()

__all__ = ["logger", "log_calls"]

# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
