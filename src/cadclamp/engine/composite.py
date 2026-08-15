from __future__ import annotations

import math


def two_tier_index(measured: float, feasible: float, recommended: float) -> float:
    """Map a measured dimension to [0, 1] against a (feasible, recommended) pair.

    ~0 at or below the hard-fail (feasible) threshold, ~1 at or above the
    recommended threshold, logistic in between. This is the Fudos-2021 shape:
    one threshold pair per rule, no other tuning.
    """
    if recommended <= feasible:
        raise ValueError("recommended must exceed feasible")
    center = (feasible + recommended) / 2.0
    scale = (recommended - feasible) / 4.0
    z = (measured - center) / scale
    z = max(-60.0, min(60.0, z))
    return 1.0 / (1.0 + math.exp(-z))


def weighted_geometric_mean(indices: dict[str, float], weights: dict[str, float] | None = None) -> float:
    """AMI-style aggregate: one very bad index tanks the composite.

    Indices are floored at 1e-6 so a hard zero yields ~0 instead of a math error.
    """
    if not indices:
        raise ValueError("no indices to aggregate")
    weights = weights or {}
    total_w = 0.0
    acc = 0.0
    for name, value in indices.items():
        w = float(weights.get(name, 1.0))
        v = min(1.0, max(1e-6, float(value)))
        acc += w * math.log(v)
        total_w += w
    return math.exp(acc / total_w)
