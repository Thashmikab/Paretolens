"""
Decision-making helpers for a Pareto front.

Every function here takes F already converted to *minimisation* and
min-max normalised to [0, 1] (0 = best value seen on the front).
The Front class does that conversion for you.
"""
import numpy as np


def nondominated_mask(F):
    """True for rows of F (minimisation) that no other row dominates."""
    F = np.asarray(F, dtype=float)
    n = len(F)
    keep = np.ones(n, dtype=bool)
    for i in range(n):
        if not keep[i]:
            continue
        # rows that are <= in every objective and < in at least one
        dominates_i = np.all(F <= F[i], axis=1) & np.any(F < F[i], axis=1)
        if dominates_i.any():
            keep[i] = False
    return keep


def normalise(F):
    """Min-max scale each column to [0, 1]. Constant columns become 0."""
    F = np.asarray(F, dtype=float)
    lo, hi = F.min(axis=0), F.max(axis=0)
    span = np.where(hi - lo == 0, 1.0, hi - lo)
    return (F - lo) / span


def knee_point(N):
    """
    Index of the knee: the point that bulges furthest towards the ideal
    from the plane f1 + f2 + ... + fm = 1 in normalised space, i.e. the plane
    through the unit points (Das, 1999; Deb & Gupta, 2011).
    """
    N = np.asarray(N, dtype=float)
    dist = (1 - N.sum(axis=1)) / np.sqrt(N.shape[1])   # >0 means towards the ideal
    return int(np.argmax(dist))


def topsis(N, weights=None):
    """
    TOPSIS closeness score for each point (higher = better).
    Ideal is 0 and anti-ideal is 1 on every normalised objective.
    """
    N = np.asarray(N, dtype=float)
    w = np.ones(N.shape[1]) if weights is None else np.asarray(weights, dtype=float)
    w = w / w.sum()
    d_best = np.sqrt((w * N ** 2).sum(axis=1))
    d_worst = np.sqrt((w * (1 - N) ** 2).sum(axis=1))
    return d_worst / (d_best + d_worst + 1e-12)


def pseudo_weights(N):
    """
    Deb's pseudo-weights: how much each objective is 'favoured' by each point.
    Rows sum to 1.
    """
    N = np.asarray(N, dtype=float)
    good = 1 - N
    total = good.sum(axis=1, keepdims=True)
    total[total == 0] = 1
    return good / total


def hypervolume_2d(N, ref=(1.1, 1.1)):
    """Area dominated by a 2-objective normalised front, up to the reference point."""
    N = np.asarray(N, dtype=float)
    pts = N[nondominated_mask(N)]
    pts = pts[np.argsort(pts[:, 0])]
    area, prev_y = 0.0, ref[1]
    for x, y in pts:
        area += (ref[0] - x) * (prev_y - y)
        prev_y = y
    return area
