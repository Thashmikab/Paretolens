# paretolens

**Explore, compare and pick solutions from a multi-objective Pareto front.**

Optimisers like NSGA-II hand you back a cloud of trade-off solutions. The hard part comes next. You have to decide which one to recommend and explain why. `paretolens` turns that front into something you can reason with. It finds the knee point, ranks solutions for any set of priorities and writes an interactive HTML page you can share with colleagues who don't use Python.

[**▶ Live demo**](https://thashmikab.github.io/paretolens/) · [ZDT1 report](https://thashmikab.github.io/paretolens/zdt1.html) · [3-objective report](https://thashmikab.github.io/paretolens/dtlz2.html) · works with [pymoo](https://pymoo.org), CSV, Excel or any NumPy array

<p align="center"><img src="docs/explainer.gif" alt="Animation: a population is filtered to its Pareto front, the knee is marked, and the best solution moves as priorities change" width="760"></p>

<details><summary>What the interactive report looks like</summary>

![paretolens report](docs/screenshot.png)

</details>

## Install

```bash
pip install git+https://github.com/Thashmikab/paretolens.git
# with pymoo for the examples
pip install "paretolens[pymoo] @ git+https://github.com/Thashmikab/paretolens.git"
# for Excel files
pip install "paretolens[excel] @ git+https://github.com/Thashmikab/paretolens.git"
```

## Use it

### Straight after a pymoo run

```python
from paretolens import Front

res = minimize(problem, NSGA2(pop_size=100), ("n_gen", 200))

# pymoo always minimises. If you maximised something by returning -f,
# mark it "max" and paretolens flips it back to its real value.
front = Front.from_pymoo(res, names=["cost", "co2", "energy"], senses=["min", "min", "max"])

front.summary()                 # extremes, knee and best compromise
front.to_html("report.html")    # interactive explorer
```

### From results you saved to a file

The only rule is **one row per solution, one column per objective**. Any other columns, such as decision variables or an id, are optional.

| solution_id | cost | co2 | energy | x1 | x2 | … |
|---|---|---|---|---|---|---|
| 0 | 1.2e6 | 340 | 5100 | … | … | |
| 1 | 1.4e6 | 310 | 5600 | … | … | |

```python
# CSV
front = Front.from_csv("results.csv", objectives={"cost": "min", "co2": "min", "energy": "max"})

# Excel, everything on one sheet
front = Front.from_excel("results.xlsx", objectives={"cost": "min", "co2": "min"},
                         sheet="results", variables=["x1", "x2"])

# Excel, objectives and decision variables on separate sheets, matched by an id column
front = Front.from_excel("results.xlsx", objectives={"cost": "min", "co2": "min"},
                         sheet="objectives", variables_sheet="decisions", on="solution_id")

# Already have a DataFrame?
front = Front.from_dataframe(df, objectives={"cost": "min", "co2": "min"})
```

Two options help with common exports:

- **`negated=["energy"]`** is for columns saved with their sign flipped. pymoo does this for a maximised objective (`-f`), so this turns them back into real values.
- **`series=True, var_label="New capacity (MW)"`** is for when the decision variables are an ordered series, such as capacity added each year. The report then draws each solution as a line over time and overlays the knee and the best pick.

### From the command line

```bash
paretolens results.csv  --min cost --min co2 --max energy -o report.html
paretolens results.xlsx --sheet objectives --min cost --max energy --negate energy
```

## What it gives you

| | |
|---|---|
| `front.summary()` | The best solution for each objective, the knee point and the best compromise, all in real units |
| `front.knee()` | The solution where improving one objective starts costing a lot in the others |
| `front.topsis({"cost": 2, "co2": 1})` | A TOPSIS score for every solution under your own priorities |
| `front.best(weights)` | The top-ranked solution for those priorities |
| `front.pseudo_weights()` | How strongly each solution favours each objective |
| `front.tradeoff(i, j, "cost", "co2")` | How much CO₂ you change per unit of cost when moving from solution *i* to *j* |
| `front.nondominated()` | Drops dominated rows if you load a whole population |
| `front.hypervolume()` | Normalised hypervolume, for comparing runs (2 objectives) |
| `front.to_html(...)` | A single-file interactive report |

The HTML report lets you pick any two objectives to plot, colour by a third, and move priority sliders to watch the best solution change. It also shows every objective on parallel coordinates, and you can click any point to see its decision variables.

## How the numbers are worked out

Each objective is turned into "smaller is better" and scaled to 0–1 across the front, so 0 is the best value found.

- **Knee point.** This is the solution furthest towards the ideal from the plane f₁ + … + fₘ = 1 (Das, 1999; Deb & Gupta, 2011). A concave front has no real knee, so there it returns an extreme point.
- **TOPSIS.** This measures weighted distance to the ideal (all 0) and to the anti-ideal (all 1). The score is closeness to the ideal, from 0 to 1 (Hwang & Yoon, 1981).
- **Pseudo-weights.** These follow Deb (2001), *Multi-Objective Optimization using Evolutionary Algorithms*.

## Examples

- [`examples/zdt1_with_pymoo.py`](examples/zdt1_with_pymoo.py) runs NSGA-II on ZDT1 and builds a report.
- [`examples/dtlz2_three_objectives.py`](examples/dtlz2_three_objectives.py) shows three objectives with a mix of minimise and maximise.

## Why I built this

My PhD work optimises UK renewable energy roadmaps against several environmental impacts of critical materials at once. NSGA-II gives hundreds of valid roadmaps, and the real question from supervisors and industry was always "so which one should we pick?" This package is the toolkit I wanted for answering that.

## Licence

MIT. Built by [Thashmika Bandara](https://github.com/Thashmikab).
