"""
Three objectives, one of them maximised, to show the min/max handling.

Uses pymoo's DTLZ2 benchmark. The third objective is flipped and renamed so the
report shows a mix of 'minimise' and 'maximise' axes.
"""
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.optimize import minimize
from pymoo.problems import get_problem
from pymoo.util.ref_dirs import get_reference_directions

from paretolens import Front

ref_dirs = get_reference_directions("das-dennis", 3, n_partitions=14)
res = minimize(get_problem("dtlz2"), NSGA3(ref_dirs=ref_dirs), ("n_gen", 300), seed=1, verbose=False)

# DTLZ2's front is a concave sphere, which has no knee. The standard
# "convex DTLZ2" transform (f1^4, f2^4, f3^2) gives a front that does.
F = res.F.copy()
F[:, :2] = F[:, :2] ** 4
F[:, 2] = 2 - F[:, 2] ** 2                 # and turn f3 into something to maximise
front = Front(F, names=["f1", "f2", "g3"], senses=["min", "min", "max"])
front.to_html("dtlz2_report.html", title="DTLZ2 · three objectives (convex)")
print(front.summary().iloc[:, :5].to_string(index=False))
