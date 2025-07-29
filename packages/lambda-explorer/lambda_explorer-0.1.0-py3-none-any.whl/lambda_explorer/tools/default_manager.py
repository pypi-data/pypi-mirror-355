from __future__ import annotations

from typing import Dict
import yaml
import os
from . import logger

# Global mapping of default values used across the GUI
default_values: Dict[str, str] = {}


def load_defaults_file(path: str = "defaults.yaml") -> None:
    """Load defaults from a YAML file into ``default_values``."""
    logger.debug("Loading defaults from %s", path)
    if not os.path.exists(path):
        logger.warning("Defaults file %s does not exist", path)
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except OSError as exc:
        logger.error("Failed to read defaults file %s: %s", path, exc)
        return
    if isinstance(data, dict):
        for var, val in data.items():
            default_values[var] = str(val)
    logger.info("Loaded %d default values", len(default_values))


def save_defaults_file(path: str = "defaults.yaml") -> None:
    """Write ``default_values`` to a YAML file."""
    logger.debug("Saving defaults to %s", path)
    try:
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(default_values, f, sort_keys=False)
        logger.info("Saved defaults to %s", path)
    except OSError as exc:
        logger.error("Failed to save defaults to %s: %s", path, exc)
