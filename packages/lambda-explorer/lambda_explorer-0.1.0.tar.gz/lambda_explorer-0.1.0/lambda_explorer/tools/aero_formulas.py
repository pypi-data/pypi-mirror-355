from __future__ import annotations

import sympy  # type: ignore

from .formula_base import Formula


class ReynoldsNumber(Formula):
    """Re = rho * V * c / mu"""

    variables = ["Re", "rho", "V", "c", "mu"]

    def __init__(self) -> None:
        Re, rho, V, c, mu = sympy.symbols("Re rho V c mu")
        eq = sympy.Eq(Re, rho * V * c / mu)
        super().__init__(self.variables, eq)


class DynamicViscosity(Formula):
    """mu = rho * V * c / Re"""

    variables = ["mu", "rho", "V", "c", "Re"]

    def __init__(self) -> None:
        mu, rho, V, c, Re = sympy.symbols("mu rho V c Re")
        eq = sympy.Eq(mu, rho * V * c / Re)
        super().__init__(self.variables, eq)


class KinematicViscosity(Formula):
    """nu = mu / rho"""

    variables = ["nu", "mu", "rho"]

    def __init__(self) -> None:
        nu, mu, rho = sympy.symbols("nu mu rho")
        eq = sympy.Eq(nu, mu / rho)
        super().__init__(self.variables, eq)

class ReEquation(ReynoldsNumber):
    """Alias for Reynolds number equation."""

class LiftEquation(Formula):
    """L = 0.5 * rho * V**2 * S * Cl"""
    variables = ["L", "rho", "V", "S", "Cl"]

    def __init__(self) -> None:
        L, rho, V, S, Cl = sympy.symbols("L rho V S Cl")
        eq = sympy.Eq(L, 0.5 * rho * V ** 2 * S * Cl)
        super().__init__(self.variables, eq)


class DragEquation(Formula):
    """D = 0.5 * rho * V**2 * S * Cd"""
    variables = ["D", "rho", "V", "S", "Cd"]

    def __init__(self) -> None:
        D, rho, V, S, Cd = sympy.symbols("D rho V S Cd")
        eq = sympy.Eq(D, 0.5 * rho * V ** 2 * S * Cd)
        super().__init__(self.variables, eq)


class MomentEquation(Formula):
    """M = 0.5 * rho * V**2 * S * c * Cm"""
    variables = ["M", "rho", "V", "S", "c", "Cm"]

    def __init__(self) -> None:
        M, rho, V, S, c, Cm = sympy.symbols("M rho V S c Cm")
        eq = sympy.Eq(M, 0.5 * rho * V ** 2 * S * c * Cm)
        super().__init__(self.variables, eq)


class DynamicPressure(Formula):
    """q = 0.5 * rho * V**2"""
    variables = ["q", "rho", "V"]

    def __init__(self) -> None:
        q, rho, V = sympy.symbols("q rho V")
        eq = sympy.Eq(q, 0.5 * rho * V ** 2)
        super().__init__(self.variables, eq)


class FrictionCoefficientLaminar(Formula):
    """Cf = 1.328 / sqrt(Re)"""
    variables = ["Cf", "Re"]

    def __init__(self) -> None:
        Cf, Re = sympy.symbols("Cf Re")
        eq = sympy.Eq(Cf, 1.328 / sympy.sqrt(Re))
        super().__init__(self.variables, eq)


class FrictionCoefficientTurbulent(Formula):
    """Cf = 0.455 / (log(Re)**2.58)"""
    variables = ["Cf", "Re"]

    def __init__(self) -> None:
        Cf, Re = sympy.symbols("Cf Re")
        eq = sympy.Eq(Cf, 0.455 / (sympy.log(Re) ** 2.58))
        super().__init__(self.variables, eq)


class BoundaryLayerThicknessLaminar(Formula):
    """delta = 5 * x / sqrt(Re)"""
    variables = ["delta", "x", "Re"]

    def __init__(self) -> None:
        delta, x, Re = sympy.symbols("delta x Re")
        eq = sympy.Eq(delta, 5 * x / sympy.sqrt(Re))
        super().__init__(self.variables, eq)


class DisplacementThicknessLaminar(Formula):
    """delta_star = 1.72 * x / sqrt(Re)"""
    variables = ["delta_star", "x", "Re"]

    def __init__(self) -> None:
        delta_star, x, Re = sympy.symbols("delta_star x Re")
        eq = sympy.Eq(delta_star, 1.72 * x / sympy.sqrt(Re))
        super().__init__(self.variables, eq)


class MomentumThicknessLaminar(Formula):
    """theta = 0.664 * x / sqrt(Re)"""
    variables = ["theta", "x", "Re"]

    def __init__(self) -> None:
        theta, x, Re = sympy.symbols("theta x Re")
        eq = sympy.Eq(theta, 0.664 * x / sympy.sqrt(Re))
        super().__init__(self.variables, eq)


class LiftCurveSlope(Formula):
    """Cl = 2 * pi * (alpha - alpha0)"""
    variables = ["Cl", "alpha", "alpha0"]

    def __init__(self) -> None:
        Cl, alpha, alpha0 = sympy.symbols("Cl alpha alpha0")
        eq = sympy.Eq(Cl, 2 * sympy.pi * (alpha - alpha0))
        super().__init__(self.variables, eq)


class InducedDrag(Formula):
    """Cd_induced = Cl**2 / (pi * AR * e)"""
    variables = ["Cd_induced", "Cl", "AR", "e"]

    def __init__(self) -> None:
        Cd_induced, Cl, AR, e = sympy.symbols("Cd_induced Cl AR e")
        eq = sympy.Eq(Cd_induced, Cl ** 2 / (sympy.pi * AR * e))
        super().__init__(self.variables, eq)


class TotalDragCoefficient(Formula):
    """Cd_total = Cd0 + k * Cl**2"""
    variables = ["Cd_total", "Cd0", "k", "Cl"]

    def __init__(self) -> None:
        Cd_total, Cd0, k, Cl = sympy.symbols("Cd_total Cd0 k Cl")
        eq = sympy.Eq(Cd_total, Cd0 + k * Cl ** 2)
        super().__init__(self.variables, eq)


class DragPolar(Formula):
    """Cd_polar = Cd0 + (Cl**2 / (pi * AR * e))"""
    variables = ["Cd_polar", "Cd0", "Cl", "AR", "e"]

    def __init__(self) -> None:
        Cd_polar, Cd0, Cl, AR, e = sympy.symbols("Cd_polar Cd0 Cl AR e")
        eq = sympy.Eq(Cd_polar, Cd0 + (Cl ** 2 / (sympy.pi * AR * e)))
        super().__init__(self.variables, eq)


class LiftAtMinDrag(Formula):
    """Cl_min_drag = sqrt(Cd0 * pi * AR * e)"""
    variables = ["Cl_min_drag", "Cd0", "AR", "e"]

    def __init__(self) -> None:
        Cl_min_drag, Cd0, AR, e = sympy.symbols("Cl_min_drag Cd0 AR e")
        eq = sympy.Eq(Cl_min_drag, sympy.sqrt(Cd0 * sympy.pi * AR * e))
        super().__init__(self.variables, eq)


class PressureCoefficient(Formula):
    """Cp = 1 - (V/V_inf)**2"""
    variables = ["Cp", "V", "V_inf"]

    def __init__(self) -> None:
        Cp, V, V_inf = sympy.symbols("Cp V V_inf")
        eq = sympy.Eq(Cp, 1 - (V / V_inf) ** 2)
        super().__init__(self.variables, eq)


class VelocityRatio(Formula):
    """V_ratio = sqrt(1 - Cp)"""
    variables = ["V_ratio", "Cp"]

    def __init__(self) -> None:
        V_ratio, Cp = sympy.symbols("V_ratio Cp")
        eq = sympy.Eq(V_ratio, sympy.sqrt(1 - Cp))
        super().__init__(self.variables, eq)


class FirstCellSpacing(Formula):
    """s = y_plus * l / (sqrt(0.013) * Re**(13/14))"""

    variables = ["s", "y_plus", "l", "Re"]

    def __init__(self) -> None:
        s, y_plus, l, Re = sympy.symbols("s y_plus l Re")
        eq = sympy.Eq(s, y_plus * l / (sympy.sqrt(0.013) * Re ** sympy.Rational(13, 14)))
        cls = self.__class__
        if not hasattr(cls, "_vars"):
            cls._vars = {name: sympy.symbols(name) for name in self.variables}
            cls.eq = eq
            args = [cls._vars[n] for n in self.variables if n != "s"]
            cls._solvers = {"s": sympy.lambdify(args, sympy.solve(eq, s)[0], "math")}
        self.vars = cls._vars
        self.eq = cls.eq
        self._solvers = cls._solvers
