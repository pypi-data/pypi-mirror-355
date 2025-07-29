from eta_ctrl import julia_extensions_available

from .math_solver import (
    MathSolver as MathSolver,
)
from .rule_based import RuleBased as RuleBased

# Import Nsga2 algorithm if julia is available and ignore errors otherwise.
if julia_extensions_available():
    from .nsga2 import Nsga2 as Nsga2
