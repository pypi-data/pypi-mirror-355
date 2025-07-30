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
import inspect


def log_calls(func: tp.Callable) -> tp.Callable:
    """Decorator logging function entry at verbose level."""

    sig = inspect.signature(func)
    params = ", ".join(str(p) for p in sig.parameters.values())
    call_params = ", ".join(p.name for p in sig.parameters.values())

    src = [f"def wrapper({params}):"]
    src.append(f"    logger.verbose('Calling {func.__qualname__}')")
    if call_params:
        src.append(f"    return func({call_params})")
    else:
        src.append("    return func()")
    namespace = {"func": func, "logger": logger}
    exec("\n".join(src), namespace)
    wrapper = wraps(func)(namespace["wrapper"])
    wrapper.__signature__ = sig

    # Preserve the original function signature so frameworks relying on
    # introspection (e.g. DearPyGui) can determine the correct callback
    # arguments even though we wrap the function.
    wrapper.__signature__ = inspect.signature(func)

    return wrapper


@log_calls
def setup_logging(level: str = "DEBUG") -> None:
    """Configure logging for the module.

    Parameters
    ----------
    level : str, optional
        Logging level passed to :func:`coloredlogs.install` and used for the
        global logger. Defaults to ``"DEBUG"``.
    """

    coloredlogs.install(level=level, logger=logger)
    logger.setLevel(level)


setup_logging()

# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------

from .tools.gui_tools import build_context_menu


@log_calls
def main() -> None:
    """Launch the Lambda Explorer GUI."""
    build_context_menu(width=800, height=600)
