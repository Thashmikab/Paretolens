"""paretolens — explore, compare and pick from multi-objective Pareto fronts."""
from .core import Front
from .decision import nondominated_mask, normalise, knee_point, topsis, pseudo_weights

__version__ = "0.1.0"
__all__ = ["Front", "nondominated_mask", "normalise", "knee_point", "topsis", "pseudo_weights"]
