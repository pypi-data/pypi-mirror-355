from __future__ import annotations

from typing import Dict, Type

from .tools.formula_base import Formula
from .tools.solver import FormulaSolver
from .tools.aero_formulas import *  # Register formulas


def run_cli() -> None:
    """Simple command line interface for solving formulas."""
    formulas: Dict[str, Type[Formula]] = {
        cls.__name__: cls for cls in Formula.__subclasses__()
    }
    while True:
        print("Available formulas:")
        for name in sorted(formulas):
            print(f"  {name}")
        choice = input("Select formula (or 'q' to quit): ").strip()
        if choice.lower() in {"q", "quit", "exit"}:
            break
        cls = formulas.get(choice)
        if not cls:
            print("Unknown formula\n")
            continue
        formula = cls()
        solver = FormulaSolver(formula)
        knowns: Dict[str, float] = {}
        missing = None
        for var in formula.variables:
            val = input(f"{var} (leave empty to solve for this): ")
            if not val.strip():
                if missing is not None:
                    print("Error: more than one variable left empty.\n")
                    break
                missing = var
            else:
                try:
                    knowns[var] = float(val)
                except ValueError:
                    print(f"Invalid value for {var}\n")
                    break
        else:
            try:
                result = solver.solve(knowns)
                print(f"{missing} = {result}\n")
            except Exception as exc:
                print(f"Error: {exc}\n")


if __name__ == "__main__":
    run_cli()


