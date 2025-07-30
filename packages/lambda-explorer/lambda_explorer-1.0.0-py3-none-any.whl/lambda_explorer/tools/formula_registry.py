from __future__ import annotations

from typing import Dict, Type, Set, List
import sympy  # type: ignore

from .formula_base import Formula
from . import logger, log_calls


class FormulaRegistry:
    """Manage discovery and storage of formula classes."""

    @log_calls
    def __init__(self) -> None:
        self.formula_classes: Dict[str, Type[Formula]] = self._discover_formulas()
        self.custom_formula_classes: Dict[str, Type[Formula]] = {}

    @log_calls
    def _gather_formulas(self, cls: Type[Formula]) -> Set[Type[Formula]]:
        found: Set[Type[Formula]] = set()
        for sub in cls.__subclasses__():
            if getattr(sub, "variables", []):
                found.add(sub)
            found.update(self._gather_formulas(sub))
        return found

    @log_calls
    def _discover_formulas(self) -> Dict[str, Type[Formula]]:
        return {cls.__name__: cls for cls in self._gather_formulas(Formula)}

    @log_calls
    def create_formula(
        self, name: str, var_names: List[str], eq: sympy.Eq
    ) -> Type[Formula]:
        def __init__(self) -> None:
            Formula.__init__(self, var_names, eq)

        cls = type(name, (Formula,), {"variables": var_names, "__init__": __init__})
        self.formula_classes[name] = cls
        self.custom_formula_classes[name] = cls
        return cls

    @log_calls
    def delete_formula(self, name: str) -> None:
        self.formula_classes.pop(name, None)
        self.custom_formula_classes.pop(name, None)

    @log_calls
    def formulas_by_topic(self) -> Dict[str, List[str]]:
        topics: Dict[str, List[str]] = {}
        for name, cls in sorted(self.formula_classes.items()):
            topic = getattr(cls, "topic", "General")
            topics.setdefault(topic, []).append(name)
        return topics


formula_registry = FormulaRegistry()
