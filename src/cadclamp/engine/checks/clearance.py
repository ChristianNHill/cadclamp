from __future__ import annotations

import numpy as np
import trimesh

from cadclamp.engine.composite import two_tier_index
from cadclamp.engine.types import FAIL, PASS, WARN, CheckResult

# Prusa: parts that must move need at least 0.3 mm between them. Shapeways
# fit classes for FDM: 0.50 loose, 0.40 normal, 0.25 tight. Below ~0.2 mm a
# 0.4 mm nozzle welds the two faces together and the assembly prints solid.
RECOMMENDED_GAP_MM = 0.4
FEASIBLE_GAP_MM = 0.2

SAMPLES_PER_BODY = 3000
SEED = 0


def _min_gap(a: trimesh.Trimesh, b: trimesh.Trimesh, samples: int, seed: int) -> float:
    """Smallest surface-to-surface distance, by sampling both ways.

    Sampling overestimates the true minimum, so both directions are taken and
    the smaller kept; on the flat and cylindrical faces these fits are made of
    that is tight enough to separate 0.2 mm from 0.5 mm.
    """
    gap = np.inf
    for source, target in ((a, b), (b, a)):
        points, _ = trimesh.sample.sample_surface(source, samples, seed=seed)
        _, distances, _ = trimesh.proximity.closest_point(target, points)
        gap = min(gap, float(np.min(distances)))
    return gap


def check_clearance(
    mesh: trimesh.Trimesh,
    *,
    recommended_mm: float = RECOMMENDED_GAP_MM,
    feasible_mm: float = FEASIBLE_GAP_MM,
    samples: int = SAMPLES_PER_BODY,
    seed: int = SEED,
) -> CheckResult:
    """Narrowest gap between separate bodies in a print-in-place assembly.

    Parts printed as one job only move afterwards if nothing in the file is
    closer than roughly one nozzle width. A single-body part has nothing to
    measure and is reported as not applicable rather than passed, so it never
    flatters a model that ignored the ask for two bodies.
    """
    thresholds = {"recommended_mm": recommended_mm, "feasible_mm": feasible_mm}
    bodies = mesh.split(only_watertight=False)
    if len(bodies) < 2:
        return CheckResult(
            check="fit_clearance",
            index=0.0,
            band=FAIL,
            measured={"body_count": int(len(bodies)), "reason": "one body: nothing is free to move"},
            thresholds=thresholds,
        )

    gap = np.inf
    pair = None
    for i in range(len(bodies)):
        for j in range(i + 1, len(bodies)):
            candidate = _min_gap(bodies[i], bodies[j], samples, seed)
            if candidate < gap:
                gap, pair = candidate, (i, j)

    index = two_tier_index(gap, feasible_mm, recommended_mm)
    if gap >= recommended_mm:
        band = PASS
    elif gap >= feasible_mm:
        band = WARN
    else:
        band = FAIL

    return CheckResult(
        check="fit_clearance",
        index=index,
        band=band,
        measured={
            "min_gap_mm": gap,
            "body_count": int(len(bodies)),
            "closest_pair": list(pair) if pair else None,
            "samples_per_body": samples,
        },
        thresholds=thresholds,
        convention="minimum surface-to-surface distance between separate bodies, seeded surface sampling both ways",
    )
