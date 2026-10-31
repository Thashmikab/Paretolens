import numpy as np
import pandas as pd
import pytest

from paretolens import Front, nondominated_mask, knee_point, topsis
from paretolens.cli import main


def convex_front(n=101):
    x = np.linspace(0, 1, n)
    return np.c_[x, 1 - np.sqrt(x)]          # ZDT1 true front, knee near the bend


def test_nondominated_filters_dominated_points():
    F = np.array([[1, 1], [2, 2], [0, 3], [3, 0], [1, 1.5]])
    assert nondominated_mask(F).tolist() == [True, False, True, True, False]


def test_knee_is_interior_on_convex_front():
    F = convex_front()
    k = knee_point(F)
    assert 5 < k < 60                         # not one of the extremes
    # knee of 1 - sqrt(x) vs the line through (0,1)-(1,0) is at x = 0.25
    assert abs(F[k, 0] - 0.25) < 0.02


def test_knee_on_linear_front_falls_back_gracefully():
    x = np.linspace(0, 1, 11)
    k = knee_point(np.c_[x, 1 - x])
    assert 0 <= k < 11


def test_topsis_respects_weights():
    F = convex_front()
    front = Front(F, ["a", "b"])
    assert front.best({"a": 1, "b": 0}) == 0                   # all about a -> a = 0
    assert front.best({"a": 0, "b": 1}) == len(F) - 1          # all about b -> b = 0
    s = topsis(front.normalised)
    assert s.shape == (len(F),) and np.all((s >= 0) & (s <= 1))


def test_max_objectives_are_flipped():
    # maximise energy, minimise cost
    F = np.array([[10, 1], [20, 2], [30, 3]])
    front = Front(F, ["energy", "cost"], ["max", "min"])
    assert front.best({"energy": 1, "cost": 0}) == 2
    assert front.best({"energy": 0, "cost": 1}) == 0
    assert len(front.nondominated()) == 3


def test_dataframe_and_summary():
    df = pd.DataFrame(convex_front(21), columns=["cost", "co2"])
    df["turbines"] = np.arange(21)
    front = Front.from_dataframe(df, {"cost": "min", "co2": "min"}, variables=["turbines"])
    s = front.summary()
    assert list(s["solution"]) == ["best cost", "best co2", "knee", "TOPSIS pick"]
    assert "turbines" in s.columns


def test_hypervolume_2d():
    front = Front(convex_front(), ["a", "b"])
    hv = front.hypervolume()
    assert 0.6 < hv < 1.21


def test_tradeoff():
    front = Front(np.array([[0, 10], [2, 6]]), ["cost", "co2"])
    assert front.tradeoff(0, 1, "cost", "co2") == -2


def test_bad_sense_raises():
    with pytest.raises(ValueError):
        Front(np.ones((3, 2)), senses=["min", "biggest"])


def test_html_and_cli(tmp_path):
    df = pd.DataFrame(convex_front(31), columns=["cost", "co2"])
    df.loc[len(df)] = [0.9, 0.9]                                 # a dominated row
    csv = tmp_path / "f.csv"
    df.to_csv(csv, index=False)
    out = tmp_path / "r.html"
    main([str(csv), "--min", "cost", "--min", "co2", "-o", str(out)])
    html = out.read_text()
    assert "plotly" in html and '"names": ["cost", "co2"]' in html
    assert html.count("[") > 31
