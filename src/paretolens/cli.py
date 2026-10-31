"""
Command line:

    paretolens results.csv --min cost --min co2 --max energy -o report.html
"""
import argparse

import pandas as pd

from .core import Front


def main(argv=None):
    ap = argparse.ArgumentParser(prog="paretolens", description="Explore a Pareto front from a CSV file.")
    ap.add_argument("csv", help="CSV with one row per solution")
    ap.add_argument("--min", action="append", default=[], metavar="COL", help="objective to minimise (repeatable)")
    ap.add_argument("--max", action="append", default=[], metavar="COL", help="objective to maximise (repeatable)")
    ap.add_argument("--vars", nargs="*", default=None, help="decision-variable columns to show alongside")
    ap.add_argument("--keep-dominated", action="store_true", help="don't filter out dominated rows")
    ap.add_argument("-o", "--out", default="pareto_report.html", help="output HTML file")
    ap.add_argument("--title", default="Pareto front explorer")
    a = ap.parse_args(argv)

    df = pd.read_csv(a.csv)
    # keep the column order from the file
    objectives = {c: ("min" if c in a.min else "max") for c in df.columns if c in a.min or c in a.max}
    missing = [c for c in a.min + a.max if c not in df.columns]
    if missing:
        ap.error(f"columns not found in CSV: {missing}")
    if len(objectives) < 2:
        ap.error("give at least two objectives with --min/--max")

    front = Front.from_dataframe(df, objectives, variables=a.vars)
    if not a.keep_dominated:
        before = len(front)
        front = front.nondominated()
        if len(front) < before:
            print(f"Dropped {before - len(front)} dominated rows.")

    print(front)
    print(front.summary().to_string(index=False))
    path = front.to_html(a.out, title=a.title)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
