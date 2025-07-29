from __future__ import annotations

from typing import Dict

from .formula_base import Formula
from . import logger


class FormulaSolver:
    """Simple wrapper around Formula providing a consistent interface."""

    def __init__(self, formula: Formula) -> None:
        self.formula = formula
        logger.debug("Created solver for %s", formula.__class__.__name__)

    def solve(self, values: Dict[str, float]) -> float:
        """Solve formula for the unknown variable using provided values."""
        logger.debug(
            "Solving %s with values %s", self.formula.__class__.__name__, values
        )
        result = self.formula.solve(**values)
        logger.verbose("Result for %s: %s", self.formula.__class__.__name__, result)
        return result
