from __future__ import annotations

from typing import Callable, Dict

import sympy  # type: ignore

from . import logger, log_calls


class Formula:
    """Base class for symbolic equations providing cached solvers."""

    variables: list[str] = []

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        for name, value in cls.__dict__.items():
            if callable(value) and not name.startswith("__"):
                setattr(cls, name, log_calls(value))

    def __init__(self, var_names: list[str], eq: sympy.Eq):
        cls = self.__class__
        if not hasattr(cls, "_vars"):
            cls._vars = {name: sympy.symbols(name) for name in var_names}
            cls.eq = eq
            cls.variables = var_names
            cls._solvers = {}
            for target, symbol in cls._vars.items():
                try:
                    sols = sympy.solve(eq, symbol)
                except Exception as exc:  # pragma: no cover - SymPy specific
                    logger.info("Unable to solve for %s: %s", target, exc)
                    continue
                if not sols:
                    logger.info("No solution for %s", target)
                    continue
                args = [v for n, v in cls._vars.items() if n != target]
                # Use Python's ``math`` module for lightweight numerical
                # evaluation to avoid importing ``numpy`` which adds
                # significant overhead.
                cls._solvers[target] = sympy.lambdify(args, sols[0], "math")
        self.vars = cls._vars
        self.eq = cls.eq
        self._solvers = cls._solvers
        logger.debug("Initialized formula %s", cls.__name__)

    def solve(self, **knowns) -> float:
        total = set(self.vars.keys())
        given = set(knowns.keys())
        extras = given - total
        if extras:
            raise ValueError(
                f"Unknown variable(s) provided: {', '.join(sorted(extras))}"
            )
        expected = len(total) - 1
        if len(given) < expected:
            missing = sorted(total - given)
            raise ValueError(
                f"{len(missing)} variable(s) missing: {', '.join(missing)}"
            )
        if len(given) > expected:
            raise ValueError(
                f"Too many variables provided (expected {expected}, got {len(given)})"
            )
        target = (total - given).pop()
        solver = self._solvers.get(target)
        if not solver:
            raise ValueError(f"No solver available for {target}")
        args = [knowns[name] for name in self.vars if name != target]
        logger.debug("Solving for %s with %s", target, knowns)
        result = float(solver(*args))
        logger.verbose("%s result %s", target, result)
        return result
