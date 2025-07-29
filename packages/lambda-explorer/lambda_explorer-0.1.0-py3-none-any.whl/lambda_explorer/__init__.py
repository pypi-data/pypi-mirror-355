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


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the module.

    Parameters
    ----------
    level : str, optional
        Logging level passed to :func:`coloredlogs.install` and used for the
        global logger. Defaults to ``"INFO"``.
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


def main() -> None:
    """Launch the Lambda Explorer GUI."""
    build_context_menu(width=800, height=600)
