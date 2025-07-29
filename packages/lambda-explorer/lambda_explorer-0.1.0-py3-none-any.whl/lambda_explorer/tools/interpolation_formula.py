from __future__ import annotations

from typing import Dict, Tuple, List
import sympy  # type: ignore

from .formula_base import Formula
from . import logger


def _linear_interpolate(x: float, x0: float, x1: float, y0: float, y1: float) -> float:
    """Return linearly interpolated value."""
    logger.debug(
        "Linear interpolate between %s=%s and %s=%s for x=%s",
        x0,
        y0,
        x1,
        y1,
        x,
    )
    if x1 == x0:
        return y0
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


class InterpolatedTableFormula(Formula):
    """Base class for formulas that use table interpolation."""

    variables: List[str] = []
    _table: Dict[float, Dict[float, List[float]]] = {}
    _distances: List[float] = []
    _initialized = False

    def __init__(self) -> None:
        cls = self.__class__
        if not cls._initialized:
            cls.vars = {name: sympy.symbols(name) for name in cls.variables}
            # Represent equation as symbolic function for display only
            result = cls.vars[cls.variables[0]]
            inputs = [cls.vars[n] for n in cls.variables[1:]]
            func = sympy.Function(cls.__name__)(*inputs)
            cls.eq = sympy.Eq(result, func)
            cls._initialized = True
        self.vars = cls.vars
        self.eq = cls.eq
        logger.debug("Initialized interpolated formula %s", cls.__name__)

    @classmethod
    def _interp_distance(
        cls, values: List[float], distance: float
    ) -> float:
        """Interpolate across the stored distance values."""
        dist = cls._distances
        if distance <= dist[0]:
            logger.debug("Distance below table range, using first value")
            return values[0]
        if distance >= dist[-1]:
            logger.debug("Distance above table range, using last value")
            return values[-1]
        for i in range(len(dist) - 1):
            if dist[i] <= distance <= dist[i + 1]:
                return _linear_interpolate(
                    distance, dist[i], dist[i + 1], values[i], values[i + 1]
                )
        raise ValueError("Distance interpolation failed")

    @classmethod
    def interpolate(cls, temp: float, mvd: float, distance: float) -> float:
        """Interpolate the table for a specific temperature, MVD and distance."""
        logger.debug(
            "Interpolating table for temp=%s mvd=%s distance=%s",
            temp,
            mvd,
            distance,
        )
        if temp not in cls._table or mvd not in cls._table[temp]:
            raise ValueError("No data for given temperature/MVD")
        values = cls._table[temp][mvd]
        return cls._interp_distance(values, distance)

    def solve(self, **knowns) -> float:
        expected = set(self.variables)
        provided = set(knowns)
        if provided - expected:
            raise ValueError(
                f"Unknown variable(s): {', '.join(sorted(provided - expected))}"
            )
        if len(provided) != len(expected) - 1:
            raise ValueError("Exactly one variable must be missing")
        missing = list(expected - provided)
        if missing[0] != self.variables[0]:
            raise ValueError(
                f"Can only solve for {self.variables[0]}, not {missing[0]}"
            )
        temp = float(knowns["temp"])
        mvd = float(knowns["mvd"])
        distance = float(knowns["distance"])
        result = self.interpolate(temp, mvd, distance)
        logger.verbose("Interpolated result: %s", result)
        return result


class ExampleIcingEquation(InterpolatedTableFormula):
    """Lookup values from icing table with interpolation across distance."""

    variables = ["icing", "distance", "temp", "mvd"]

    # Distances used in the table
    _distances = [0.26, 0.5, 1.0, 1.5, 2.6, 4.0, 5.0]

    # Table data structured as temp -> mvd -> list of values for each distance
    _table = {
        0.0: {
            5.0: [1.350, 1.295, 1.190, 1.115, 1.000, 0.905, 0.860],
            15.0: [3.915, 3.756, 3.451, 3.234, 2.900, 2.625, 2.494],
            20.0: [3.375, 3.238, 2.975, 2.788, 2.500, 2.263, 2.150],
            25.0: [2.363, 2.266, 2.083, 1.951, 1.750, 1.582, 1.505],
            30.0: [1.789, 1.716, 1.577, 1.477, 1.325, 1.199, 1.140],
            40.0: [1.013, 0.971, 0.893, 0.836, 0.750, 0.679, 0.645],
        },
        -10.0: {
            15.0: [3.375, 3.238, 2.975, 2.788, 2.500, 2.263, 2.150],
            20.0: [2.970, 2.849, 2.618, 2.453, 2.200, 1.991, 1.892],
            25.0: [1.958, 1.878, 1.726, 1.617, 1.450, 1.312, 1.247],
            30.0: [1.384, 1.327, 1.220, 1.143, 1.025, 0.928, 0.882],
            35.0: [0.962, 0.923, 0.848, 0.794, 0.713, 0.645, 0.613],
            40.0: [0.692, 0.664, 0.610, 0.571, 0.513, 0.464, 0.441],
        },
        -20.0: {
            15.0: [2.599, 2.493, 2.291, 2.146, 1.925, 1.742, 1.656],
            20.0: [2.295, 2.202, 2.023, 1.896, 1.700, 1.539, 1.462],
            25.0: [1.553, 1.489, 1.369, 1.282, 1.150, 1.041, 0.989],
            30.0: [1.080, 1.036, 0.952, 0.892, 0.800, 0.724, 0.688],
            35.0: [0.776, 0.745, 0.684, 0.641, 0.575, 0.520, 0.495],
            40.0: [0.540, 0.518, 0.476, 0.446, 0.400, 0.362, 0.344],
        },
        -30.0: {
            15.0: [1.485, 1.425, 1.309, 1.227, 1.100, 0.996, 0.946],
            20.0: [1.333, 1.279, 1.175, 1.101, 0.988, 0.894, 0.849],
            25.0: [0.962, 0.923, 0.848, 0.794, 0.713, 0.645, 0.613],
            30.0: [0.675, 0.648, 0.595, 0.558, 0.500, 0.453, 0.430],
            35.0: [0.473, 0.453, 0.417, 0.390, 0.350, 0.317, 0.301],
            40.0: [0.338, 0.324, 0.298, 0.279, 0.250, 0.226, 0.215],
        },
    }

