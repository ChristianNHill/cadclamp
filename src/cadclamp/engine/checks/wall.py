from __future__ import annotations

import numpy as np
import trimesh

from cadclamp.engine.composite import two_tier_index
from cadclamp.engine.types import FAIL, PASS, WARN, CheckResult

# Robust statistic: a low percentile rather than the raw minimum guards
# against isolated sampling artifacts without letting a genuinely thin wall
# hide. Vendor tools ship equivalent guards (Magics "wall angle",
# SOLIDWORKS "treat corners as zero thickness").
THIN_PERCENTILE = 2.0


def _sample_surface(mesh: trimesh.Trimesh, count: int, seed: int):
    try:
        points, face_index = trimesh.sample.sample_surface(mesh, count, seed=seed)
    except TypeError:  # older trimesh without the seed kwarg
        rng_state = np.random.get_state()
        np.random.seed(seed)
        try:
            points, face_index = trimesh.sample.sample_surface(mesh, count)
        finally:
            np.random.set_state(rng_state)
    return points, face_index


def check_min_wall(
    mesh: trimesh.Trimesh,
    *,
    line_width_mm: float = 0.4,
    recommended_mm: float | None = None,
    feasible_mm: float | None = None,
    samples: int = 800,
    seed: int = 0,
) -> CheckResult:
    """Minimum wall thickness via ray chords along inverted surface normals.

    v0 method note: the max-inscribed-sphere method reads distance-to-edge on
    blocky parts (the sphere gets pinched at convex corners — a solid cube
    scores as paper-thin), so the mesh-level check uses the ray-chord method
    instead. Known limitation: it overestimates oblique walls by 1/cos(tilt);
    the B-rep exact face-pair distance in the scoring container is the
    authoritative measurement and supersedes this. Thresholds are multiples
    of the extrusion line width so the rule is nozzle-agnostic:
    recommended = 2 lines (0.8 mm @ 0.4), feasible = ~1 perimeter (0.45 mm).
    """
    recommended = recommended_mm if recommended_mm is not None else 2.0 * line_width_mm
    feasible = feasible_mm if feasible_mm is not None else 1.125 * line_width_mm

    points, face_index = _sample_surface(mesh, samples, seed)
    normals = mesh.face_normals[face_index]
    thickness = trimesh.proximity.thickness(mesh, points, normals=normals, method="ray")
    finite = np.asarray(thickness)[np.isfinite(thickness)]

    if len(finite) == 0:
        return CheckResult(
            check="min_wall",
            index=0.0,
            band=FAIL,
            measured={"reason": "no finite thickness samples"},
            thresholds={"recommended_mm": recommended, "feasible_mm": feasible},
        )

    thin = float(np.percentile(finite, THIN_PERCENTILE))
    index = two_tier_index(thin, feasible, recommended)
    if thin >= recommended:
        band = PASS
    elif thin >= feasible:
        band = WARN
    else:
        band = FAIL

    return CheckResult(
        check="min_wall",
        index=index,
        band=band,
        measured={
            "thin_wall_p2_mm": thin,
            "median_mm": float(np.median(finite)),
            "min_mm": float(finite.min()),
            "finite_samples": int(len(finite)),
            "total_samples": int(samples),
        },
        thresholds={
            "recommended_mm": recommended,
            "feasible_mm": feasible,
            "line_width_mm": line_width_mm,
        },
        convention=f"ray chord along inverted normal, p{THIN_PERCENTILE:g} over seeded surface samples",
    )
