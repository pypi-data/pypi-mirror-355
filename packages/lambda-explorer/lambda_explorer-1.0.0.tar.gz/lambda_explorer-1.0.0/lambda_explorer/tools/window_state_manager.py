from __future__ import annotations

import json
import os
from typing import List

from . import logger, log_calls

WINDOWS_FILE = "open_windows.json"


@log_calls
def load_open_windows(path: str = WINDOWS_FILE) -> List[str]:
    """Return list of formula names that were open last session."""
    logger.debug("Loading open windows from %s", path)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(x) for x in data]
    except Exception as exc:  # pragma: no cover - GUI
        logger.warning("Could not load open windows: %s", exc)
    return []


@log_calls
def save_open_windows(windows: List[str], path: str = WINDOWS_FILE) -> None:
    """Store the list of open formula window names."""
    logger.debug("Saving open windows to %s", path)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(windows, f)
        logger.info("Saved open windows to %s", path)
    except Exception as exc:  # pragma: no cover - GUI
        logger.warning("Could not save open windows: %s", exc)
