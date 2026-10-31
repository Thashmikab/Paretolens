"""
Run NSGA-II on the ZDT1 benchmark with pymoo, then explore the front.

    pip install "paretolens[pymoo]"
    python examples/zdt1_with_pymoo.py
"""
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.problems import get_problem

from paretolens import Front

res = minimize(get_problem("zdt1"), NSGA2(pop_size=100), ("n_gen", 200), seed=1, verbose=False)

front = Front.from_pymoo(res, names=["f1", "f2"],
                         var_names=[f"x{i + 1}" for i in range(res.X.shape[1])])
print(front)
print(front.summary().iloc[:, :4].to_string(index=False))
front.to_html("zdt1_report.html", title="ZDT1 · NSGA-II front")
print("Open zdt1_report.html in a browser.")
