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

    topic = "Aerodynamics"


class LiftEquation(Formula):
    """L = 0.5 * rho * V**2 * S * Cl"""

    topic = "Aerodynamics"
    variables = ["L", "rho", "V", "S", "Cl"]

    def __init__(self) -> None:
        L, rho, V, S, Cl = sympy.symbols("L rho V S Cl")
        eq = sympy.Eq(L, 0.5 * rho * V**2 * S * Cl)
        super().__init__(self.variables, eq)


class DragEquation(Formula):
    """D = 0.5 * rho * V**2 * S * Cd"""

    topic = "Aerodynamics"
    variables = ["D", "rho", "V", "S", "Cd"]

    def __init__(self) -> None:
        D, rho, V, S, Cd = sympy.symbols("D rho V S Cd")
        eq = sympy.Eq(D, 0.5 * rho * V**2 * S * Cd)
        super().__init__(self.variables, eq)


class MomentEquation(Formula):
    """M = 0.5 * rho * V**2 * S * c * Cm"""

    topic = "Aerodynamics"
    variables = ["M", "rho", "V", "S", "c", "Cm"]

    def __init__(self) -> None:
        M, rho, V, S, c, Cm = sympy.symbols("M rho V S c Cm")
        eq = sympy.Eq(M, 0.5 * rho * V**2 * S * c * Cm)
        super().__init__(self.variables, eq)


class DynamicPressure(Formula):
    """q = 0.5 * rho * V**2"""

    topic = "Aerodynamics"
    variables = ["q", "rho", "V"]

    def __init__(self) -> None:
        q, rho, V = sympy.symbols("q rho V")
        eq = sympy.Eq(q, 0.5 * rho * V**2)
        super().__init__(self.variables, eq)


class FrictionCoefficientLaminar(Formula):
    """Cf = 1.328 / sqrt(Re)"""

    topic = "Aerodynamics"
    variables = ["Cf", "Re"]

    def __init__(self) -> None:
        Cf, Re = sympy.symbols("Cf Re")
        eq = sympy.Eq(Cf, 1.328 / sympy.sqrt(Re))
        super().__init__(self.variables, eq)


class FrictionCoefficientTurbulent(Formula):
    """Cf = 0.455 / (log(Re)**2.58)"""

    topic = "Aerodynamics"
    variables = ["Cf", "Re"]

    def __init__(self) -> None:
        Cf, Re = sympy.symbols("Cf Re")
        eq = sympy.Eq(Cf, 0.455 / (sympy.log(Re) ** 2.58))
        super().__init__(self.variables, eq)


class BoundaryLayerThicknessLaminar(Formula):
    """delta = 5 * x / sqrt(Re)"""

    topic = "Aerodynamics"
    variables = ["delta", "x", "Re"]

    def __init__(self) -> None:
        delta, x, Re = sympy.symbols("delta x Re")
        eq = sympy.Eq(delta, 5 * x / sympy.sqrt(Re))
        super().__init__(self.variables, eq)


class DisplacementThicknessLaminar(Formula):
    """delta_star = 1.72 * x / sqrt(Re)"""

    topic = "Aerodynamics"
    variables = ["delta_star", "x", "Re"]

    def __init__(self) -> None:
        delta_star, x, Re = sympy.symbols("delta_star x Re")
        eq = sympy.Eq(delta_star, 1.72 * x / sympy.sqrt(Re))
        super().__init__(self.variables, eq)


class MomentumThicknessLaminar(Formula):
    """theta = 0.664 * x / sqrt(Re)"""

    topic = "Aerodynamics"
    variables = ["theta", "x", "Re"]

    def __init__(self) -> None:
        theta, x, Re = sympy.symbols("theta x Re")
        eq = sympy.Eq(theta, 0.664 * x / sympy.sqrt(Re))
        super().__init__(self.variables, eq)


class LiftCurveSlope(Formula):
    """Cl = 2 * pi * (alpha - alpha0)"""

    topic = "Aerodynamics"
    variables = ["Cl", "alpha", "alpha0"]

    def __init__(self) -> None:
        Cl, alpha, alpha0 = sympy.symbols("Cl alpha alpha0")
        eq = sympy.Eq(Cl, 2 * sympy.pi * (alpha - alpha0))
        super().__init__(self.variables, eq)


class InducedDrag(Formula):
    """Cd_induced = Cl**2 / (pi * AR * e)"""

    topic = "Aerodynamics"
    variables = ["Cd_induced", "Cl", "AR", "e"]

    def __init__(self) -> None:
        Cd_induced, Cl, AR, e = sympy.symbols("Cd_induced Cl AR e")
        eq = sympy.Eq(Cd_induced, Cl**2 / (sympy.pi * AR * e))
        super().__init__(self.variables, eq)


class TotalDragCoefficient(Formula):
    """Cd_total = Cd0 + k * Cl**2"""

    topic = "Aerodynamics"
    variables = ["Cd_total", "Cd0", "k", "Cl"]

    def __init__(self) -> None:
        Cd_total, Cd0, k, Cl = sympy.symbols("Cd_total Cd0 k Cl")
        eq = sympy.Eq(Cd_total, Cd0 + k * Cl**2)
        super().__init__(self.variables, eq)


class DragPolar(Formula):
    """Cd_polar = Cd0 + (Cl**2 / (pi * AR * e))"""

    topic = "Aerodynamics"
    variables = ["Cd_polar", "Cd0", "Cl", "AR", "e"]

    def __init__(self) -> None:
        Cd_polar, Cd0, Cl, AR, e = sympy.symbols("Cd_polar Cd0 Cl AR e")
        eq = sympy.Eq(Cd_polar, Cd0 + (Cl**2 / (sympy.pi * AR * e)))
        super().__init__(self.variables, eq)


class LiftAtMinDrag(Formula):
    """Cl_min_drag = sqrt(Cd0 * pi * AR * e)"""

    topic = "Aerodynamics"
    variables = ["Cl_min_drag", "Cd0", "AR", "e"]

    def __init__(self) -> None:
        Cl_min_drag, Cd0, AR, e = sympy.symbols("Cl_min_drag Cd0 AR e")
        eq = sympy.Eq(Cl_min_drag, sympy.sqrt(Cd0 * sympy.pi * AR * e))
        super().__init__(self.variables, eq)


class PressureCoefficient(Formula):
    """Cp = 1 - (V/V_inf)**2"""

    topic = "Aerodynamics"
    variables = ["Cp", "V", "V_inf"]

    def __init__(self) -> None:
        Cp, V, V_inf = sympy.symbols("Cp V V_inf")
        eq = sympy.Eq(Cp, 1 - (V / V_inf) ** 2)
        super().__init__(self.variables, eq)


class VelocityRatio(Formula):
    """V_ratio = sqrt(1 - Cp)"""

    topic = "Aerodynamics"
    variables = ["V_ratio", "Cp"]

    def __init__(self) -> None:
        V_ratio, Cp = sympy.symbols("V_ratio Cp")
        eq = sympy.Eq(V_ratio, sympy.sqrt(1 - Cp))
        super().__init__(self.variables, eq)


class FirstCellSpacing(Formula):
    """s = y_plus * l / (sqrt(0.013) * Re**(13/14))"""

    topic = "Aerodynamics"

    variables = ["s", "y_plus", "l", "Re"]

    def __init__(self) -> None:
        s, y_plus, l, Re = sympy.symbols("s y_plus l Re")
        eq = sympy.Eq(
            s, y_plus * l / (sympy.sqrt(0.013) * Re ** sympy.Rational(13, 14))
        )
        cls = self.__class__
        if not hasattr(cls, "_vars"):
            cls._vars = {name: sympy.symbols(name) for name in self.variables}
            cls.eq = eq
            args = [cls._vars[n] for n in self.variables if n != "s"]
            cls._solvers = {"s": sympy.lambdify(args, sympy.solve(eq, s)[0], "math")}
        self.vars = cls._vars
        self.eq = cls.eq
        self._solvers = cls._solvers


# ----------------------------------------------------------------------------
# Thermodynamic Fundamentals
# ----------------------------------------------------------------------------


class IdealGasLaw(Formula):
    """p = ρ * R * T"""

    topic = "Theromdynamics"

    variables = ["p", "rho", "R", "T"]

    def __init__(self):
        p, rho, R, T = sympy.symbols("p rho R T")
        eq = sympy.Eq(p, rho * R * T)
        super().__init__(self.variables, eq)


class AdiabaticPressureVolume(Formula):
    """p * v^κ = C (constant)"""

    topic = "Theromdynamics"

    variables = ["p", "v", "kappa", "C"]

    def __init__(self):
        p, v, kappa, C = sympy.symbols("p v kappa C")
        eq = sympy.Eq(p * v**kappa, C)
        super().__init__(self.variables, eq)


class AdiabaticTemperatureVolume(Formula):
    """T * v^{κ−1} = C (constant)"""

    topic = "Theromdynamics"

    variables = ["T", "v", "kappa", "C"]

    def __init__(self):
        T, v, kappa, C = sympy.symbols("T v kappa C")
        eq = sympy.Eq(T * v ** (kappa - 1), C)
        super().__init__(self.variables, eq)


class AdiabaticTemperaturePressure(Formula):
    """T * p^{(1−κ)/κ} = C (constant)"""

    topic = "Theromdynamics"

    variables = ["T", "p", "kappa", "C"]

    def __init__(self):
        T, p, kappa, C = sympy.symbols("T p kappa C")
        exponent = (1 - kappa) / kappa
        eq = sympy.Eq(T * p**exponent, C)
        super().__init__(self.variables, eq)


# ----------------------------------------------------------------------------
# Isentropic Flow Relations (Mach‑dependent)
# ----------------------------------------------------------------------------


class MachTemperatureRatio(Formula):
    """T / T0 = 1 + (κ−1)/2 · Ma²"""

    topic = "Theromdynamics"

    variables = ["T", "T0", "kappa", "Ma"]

    def __init__(self):
        T, T0, kappa, Ma = sympy.symbols("T T0 kappa Ma")
        eq = sympy.Eq(T / T0, 1 + (kappa - 1) / 2 * Ma**2)
        super().__init__(self.variables, eq)


class MachPressureRatio(Formula):
    """p / p0 = (1 + (κ−1)/2 · Ma²)^{−κ/(κ−1)}"""

    topic = "Theromdynamics"

    variables = ["p", "p0", "kappa", "Ma"]

    def __init__(self):
        p, p0, kappa, Ma = sympy.symbols("p p0 kappa Ma")
        eq = sympy.Eq(p / p0, (1 + (kappa - 1) / 2 * Ma**2) ** (-kappa / (kappa - 1)))
        super().__init__(self.variables, eq)


class MachDensityRatio(Formula):
    """ρ / ρ0 = (1 + (κ−1)/2 · Ma²)^{−1/(κ−1)}"""

    topic = "Theromdynamics"

    variables = ["rho", "rho0", "kappa", "Ma"]

    def __init__(self):
        rho, rho0, kappa, Ma = sympy.symbols("rho rho0 kappa Ma")
        eq = sympy.Eq(rho / rho0, (1 + (kappa - 1) / 2 * Ma**2) ** (-1 / (kappa - 1)))
        super().__init__(self.variables, eq)


# ----------------------------------------------------------------------------
# Energy Relation
# ----------------------------------------------------------------------------


class EnergyEquation(Formula):
    """w² / 2 = h₀ − h"""

    topic = "Theromdynamics"

    variables = ["w", "h0", "h"]

    def __init__(self):
        w, h0, h = sympy.symbols("w h0 h")
        eq = sympy.Eq(w**2 / 2, h0 - h)
        super().__init__(self.variables, eq)


# ----------------------------------------------------------------------------
# Thrust & Performance Metrics
# ----------------------------------------------------------------------------


class ThrustEquation(Formula):
    """F = ṁ · w_e + (p_e − p_a) · A_e"""

    topic = "Theromdynamics"

    variables = ["F", "mdot", "w_e", "p_e", "p_a", "A_e"]

    def __init__(self):
        F, mdot, w_e, p_e, p_a, A_e = sympy.symbols("F mdot w_e p_e p_a A_e")
        eq = sympy.Eq(F, mdot * w_e + (p_e - p_a) * A_e)
        super().__init__(self.variables, eq)


class EffectiveExhaustVelocity(Formula):
    """c_e = w_e + (p_e − p_a) · A_e / ṁ"""

    topic = "Theromdynamics"

    variables = ["c_e", "w_e", "p_e", "p_a", "A_e", "mdot"]

    def __init__(self):
        c_e, w_e, p_e, p_a, A_e, mdot = sympy.symbols("c_e w_e p_e p_a A_e mdot")
        eq = sympy.Eq(c_e, w_e + (p_e - p_a) * A_e / mdot)
        super().__init__(self.variables, eq)


class SpecificImpulse(Formula):
    """I_sp = F / (ṁ · g₀)"""

    topic = "Theromdynamics"

    variables = ["I_sp", "F", "mdot", "g0"]

    def __init__(self):
        I_sp, F, mdot, g0 = sympy.symbols("I_sp F mdot g0")
        eq = sympy.Eq(I_sp, F / (mdot * g0))
        super().__init__(self.variables, eq)


class ThrustCoefficient(Formula):
    """c_F = F / (p₀ · A_t)"""

    topic = "Theromdynamics"

    variables = ["c_F", "F", "p0", "A_t"]

    def __init__(self):
        c_F, F, p0, A_t = sympy.symbols("c_F F p0 A_t")
        eq = sympy.Eq(c_F, F / (p0 * A_t))
        super().__init__(self.variables, eq)


class MassFlowRate(Formula):
    """ṁ = (p₀ · A_t / √(R · T₀)) · Γ(κ)"""

    topic = "Theromdynamics"

    variables = ["mdot", "p0", "A_t", "R", "T0", "Gamma"]

    def __init__(self):
        mdot, p0, A_t, R, T0, Gamma = sympy.symbols("mdot p0 A_t R T0 Gamma")
        eq = sympy.Eq(mdot, (p0 * A_t / sympy.sqrt(R * T0)) * Gamma)
        super().__init__(self.variables, eq)


# ----------------------------------------------------------------------------
# Auxiliary Functions
# ----------------------------------------------------------------------------


class GammaFunction(Formula):
    """Γ(κ) = √κ · (2 / (κ + 1))^{(κ + 1)/(2(κ − 1))}"""

    topic = "Theromdynamics"

    variables = ["Gamma", "kappa"]

    def __init__(self):
        Gamma, kappa = sympy.symbols("Gamma kappa")
        eq = sympy.Eq(
            Gamma,
            sympy.sqrt(kappa) * (2 / (kappa + 1)) ** ((kappa + 1) / (2 * (kappa - 1))),
        )
        super().__init__(self.variables, eq)


class CharacteristicLength(Formula):
    """L* = V₀ / A_t"""

    topic = "Theromdynamics"

    variables = ["L_star", "V0", "A_t"]

    def __init__(self):
        L_star, V0, A_t = sympy.symbols("L_star V0 A_t")
        eq = sympy.Eq(L_star, V0 / A_t)
        super().__init__(self.variables, eq)


class CharacteristicVelocity(Formula):
    """c* = √(R · T₀) / Γ(κ)"""

    topic = "Theromdynamics"

    variables = ["c_star", "R", "T0", "Gamma"]

    def __init__(self):
        c_star, R, T0, Gamma = sympy.symbols("c_star R T0 Gamma")
        eq = sympy.Eq(c_star, sympy.sqrt(R * T0) / Gamma)
        super().__init__(self.variables, eq)
