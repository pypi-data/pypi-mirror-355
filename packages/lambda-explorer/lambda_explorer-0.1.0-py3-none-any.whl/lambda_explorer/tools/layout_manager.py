from __future__ import annotations

import os
import dearpygui.dearpygui as dpg
from . import logger

LAYOUT_FILE = "layout.ini"


def load_layout(path: str = LAYOUT_FILE) -> None:
    """Load window layout from an ini file if it exists."""
    logger.debug("Loading layout from %s", path)
    if os.path.exists(path):
        try:
            dpg.load_init_file(path)
            logger.info("Layout loaded from %s", path)
        except Exception as exc:  # pragma: no cover - GUI
            logger.warning("Could not load layout: %s", exc)


def save_layout(path: str = LAYOUT_FILE) -> None:
    """Save current window layout to an ini file."""
    logger.debug("Saving layout to %s", path)
    try:
        dpg.save_init_file(path)
        logger.info("Layout saved to %s", path)
    except Exception as exc:  # pragma: no cover - GUI
        logger.warning("Could not save layout: %s", exc)
