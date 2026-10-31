import numpy as np
import pandas as pd

from . import decision


class Front:
    """
    A set of trade-off solutions.

    F       : objective values, shape (n_points, n_objectives), in their real units
    names   : objective names, e.g. ["cost", "co2", "copper"]
    senses  : "min" or "max" for each objective (default: all "min")
    X       : optional decision variables, shape (n_points, n_vars)
    series  : True if X is an ordered series (e.g. capacity added each year), so the
              report draws each solution's X as a line instead of listing the values
    var_label : y-axis label for that line, e.g. "New capacity (MW)"
    """

    def __init__(self, F, names=None, senses=None, X=None, var_names=None, units=None,
                 series=False, var_label=None):
        self.F = np.atleast_2d(np.asarray(F, dtype=float))
        n, m = self.F.shape
        self.names = list(names) if names is not None else [f"f{i + 1}" for i in range(m)]
        self.senses = list(senses) if senses is not None else ["min"] * m
        self.units = list(units) if units is not None else [""] * m
        if len(self.names) != m or len(self.senses) != m or len(self.units) != m:
            raise ValueError("names, senses and units must have one entry per objective")
        for s in self.senses:
            if s not in ("min", "max"):
                raise ValueError(f"sense must be 'min' or 'max', got {s!r}")

        self.X = None if X is None else np.atleast_2d(np.asarray(X, dtype=float))
        if self.X is not None and len(self.X) != n:
            raise ValueError("X must have the same number of rows as F")
        if self.X is not None:
            self.var_names = list(var_names) if var_names is not None else [
                f"x{i + 1}" for i in range(self.X.shape[1])]
        else:
            self.var_names = []
        self.series = bool(series) and self.X is not None
        self.var_label = var_label or "value"

    # ---------- loading ----------

    @classmethod
    def from_dataframe(cls, df, objectives, variables=None, negated=None, units=None,
                       series=False, var_label=None):
        """
        One row per solution.

        objectives: {"column": "min" | "max"}, in the order you want them
        variables : optional list of decision-variable columns to carry along
        negated   : columns saved with their sign flipped, as pymoo does when you
                    maximise by minimising -f. They are flipped back on loading.
        """
        names = list(objectives)
        missing = [c for c in names + list(variables or []) if c not in df.columns]
        if missing:
            raise KeyError(f"columns not found: {missing}. Available: {list(df.columns)}")
        F = df[names].to_numpy(dtype=float).copy()
        for c in negated or []:
            if c not in names:
                raise KeyError(f"negated column {c!r} is not one of the objectives")
            F[:, names.index(c)] *= -1
        X = df[variables].to_numpy() if variables else None
        return cls(F, names, [objectives[k] for k in names],
                   X=X, var_names=[str(v) for v in variables] if variables else None,
                   units=units, series=series, var_label=var_label)

    @classmethod
    def from_csv(cls, path, objectives, variables=None, negated=None, units=None,
                 series=False, var_label=None, **read_kwargs):
        """Same as from_dataframe, reading a CSV with one row per solution."""
        return cls.from_dataframe(pd.read_csv(path, **read_kwargs), objectives, variables,
                                  negated, units, series, var_label)

    @classmethod
    def from_excel(cls, path, objectives, sheet=0, variables=None, variables_sheet=None,
                   on=None, negated=None, units=None, series=False, var_label=None):
        """
        Read an Excel file with one row per solution.

        Simple case: objectives (and optionally variables) are columns in one sheet.
        Split case : objectives in `sheet`, decision variables in `variables_sheet`,
                     matched row by row through a shared id column `on`. If
                     `variables` is not given, every other column of that sheet is used.
        """
        df = pd.read_excel(path, sheet_name=sheet)
        if variables_sheet is not None:
            xv = pd.read_excel(path, sheet_name=variables_sheet)
            if on is None:
                if len(xv) != len(df):
                    raise ValueError("sheets have different row counts; pass `on` with the id column")
                xv = xv.set_index(df.index)
                df = pd.concat([df, xv.drop(columns=[c for c in xv.columns if c in df.columns])], axis=1)
            else:
                df = df.merge(xv, on=on, suffixes=("", "_var"))
            if variables is None:
                variables = [c for c in xv.columns if c != on and c not in objectives]
        return cls.from_dataframe(df, objectives, variables, negated, units, series, var_label)

    @classmethod
    def from_pymoo(cls, res, names=None, senses=None, var_names=None, units=None,
                   series=False, var_label=None):
        """
        Build from a pymoo Result. pymoo always minimises, so for an objective you
        maximised by returning -f, pass senses=[..., "max", ...] and the sign is undone.
        """
        F = np.array(res.F, dtype=float)
        senses = senses or ["min"] * F.shape[1]
        for j, s in enumerate(senses):
            if s == "max":
                F[:, j] = -F[:, j]
        X = getattr(res, "X", None)
        if X is not None and np.asarray(X).dtype == object:
            X = None                                   # mixed-variable results: skip
        return cls(F, names, senses, X=X, var_names=var_names, units=units,
                   series=series, var_label=var_label)

    # ---------- basic views ----------

    def __len__(self):
        return len(self.F)

    @property
    def F_min(self):
        """Objectives flipped so that every column is 'smaller is better'."""
        sign = np.array([1 if s == "min" else -1 for s in self.senses])
        return self.F * sign

    @property
    def normalised(self):
        """0 = best value on the front, 1 = worst, for every objective."""
        return decision.normalise(self.F_min)

    def to_dataframe(self):
        df = pd.DataFrame(self.F, columns=self.names)
        if self.X is not None:
            df = pd.concat([df, pd.DataFrame(self.X, columns=self.var_names)], axis=1)
        return df

    def _subset(self, mask):
        return Front(self.F[mask], self.names, self.senses,
                     None if self.X is None else self.X[mask], self.var_names or None, self.units,
                     self.series, self.var_label)

    def nondominated(self):
        """Drop any dominated points (useful if you load a whole population)."""
        return self._subset(decision.nondominated_mask(self.F_min))

    # ---------- decision support ----------

    def knee(self):
        """Index of the knee point."""
        return decision.knee_point(self.normalised)

    def topsis(self, weights=None):
        """TOPSIS score per point (higher is better). weights can be a list or {name: w}."""
        return decision.topsis(self.normalised, self._weights(weights))

    def best(self, weights=None):
        """Index of the top TOPSIS solution for the given weights."""
        return int(np.argmax(self.topsis(weights)))

    def pseudo_weights(self):
        return pd.DataFrame(decision.pseudo_weights(self.normalised), columns=self.names)

    def hypervolume(self):
        """Normalised hypervolume (2 objectives only)."""
        if self.F.shape[1] != 2:
            raise NotImplementedError("hypervolume is only built in for 2 objectives; use pymoo's HV for more")
        return decision.hypervolume_2d(self.normalised)

    def tradeoff(self, i, j, a, b):
        """
        How much of objective b you give up per unit of objective a gained
        when moving from solution i to solution j (real units).
        """
        ia, ib = self.names.index(a), self.names.index(b)
        da = self.F[j, ia] - self.F[i, ia]
        db = self.F[j, ib] - self.F[i, ib]
        return np.inf if da == 0 else db / da

    def _weights(self, weights):
        if weights is None:
            return None
        if isinstance(weights, dict):
            return [weights.get(n, 0.0) for n in self.names]
        return list(weights)

    def summary(self, weights=None):
        """Table of the extreme points, the knee and the TOPSIS pick, in real units."""
        rows, labels = [], []
        for j, n in enumerate(self.names):
            rows.append(int(np.argmin(self.F_min[:, j])))
            labels.append(f"best {n}")
        rows += [self.knee(), self.best(weights)]
        labels += ["knee", "TOPSIS pick"]
        out = self.to_dataframe().iloc[rows].copy()
        out.insert(0, "solution", labels)
        out.insert(1, "index", rows)
        return out.reset_index(drop=True)

    # ---------- output ----------

    def to_html(self, path, title="Pareto front explorer", weights=None):
        from .report import write_html
        return write_html(self, path, title=title, weights=weights)

    def __repr__(self):
        objs = ", ".join(f"{n} ({s})" for n, s in zip(self.names, self.senses))
        return f"Front({len(self)} points: {objs})"
