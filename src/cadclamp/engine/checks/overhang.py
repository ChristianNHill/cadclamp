from __future__ import annotations

import numpy as np
import trimesh

from cadclamp.engine.types import FAIL, PASS, WARN, CheckResult

# Severity weights for the v0 heuristic index; warn-band area costs a
# fraction of fail-band area. Documented, not tuned.
WARN_WEIGHT = 0.35
FAIL_WEIGHT = 1.0
BAND_FAIL_AREA_FRACTION = 0.05
BAND_WARN_AREA_FRACTION = 0.10


def check_overhang(
    mesh: trimesh.Trimesh,
    *,
    warn_deg: float = 45.0,
    fail_deg: float = 60.0,
    layer_mm: float = 0.2,
) -> CheckResult:
    """Area-weighted overhang bands.

    Convention (stated because slicers genuinely disagree, two of them in
    opposite directions): the overhang angle is measured FROM VERTICAL with
    build direction +Z. A vertical wall is 0 deg; a bare horizontal downface
    is 90 deg. Faces whose centroid sits in the first-layer band are bed
    contact, not overhang.
    """
    normals = mesh.face_normals
    # downward component of the outward normal = sin(angle from vertical)
    theta = np.degrees(np.arcsin(np.clip(-normals[:, 2], 0.0, 1.0)))
    areas = mesh.area_faces
    z_min = float(mesh.bounds[0][2])
    relevant = mesh.triangles_center[:, 2] > (z_min + layer_mm)

    total_area = float(areas.sum())
    warn_mask = relevant & (theta > warn_deg) & (theta <= fail_deg)
    fail_mask = relevant & (theta > fail_deg)
    warn_fraction = float(areas[warn_mask].sum() / total_area) if total_area > 0 else 0.0
    fail_fraction = float(areas[fail_mask].sum() / total_area) if total_area > 0 else 0.0

    index = max(0.0, 1.0 - WARN_WEIGHT * warn_fraction - FAIL_WEIGHT * fail_fraction)
    if fail_fraction > BAND_FAIL_AREA_FRACTION:
        band = FAIL
    elif warn_fraction > BAND_WARN_AREA_FRACTION:
        band = WARN
    else:
        band = PASS

    return CheckResult(
        check="overhang",
        index=index,
        band=band,
        measured={
            "warn_area_fraction": warn_fraction,
            "fail_area_fraction": fail_fraction,
            "max_overhang_deg": float(theta[relevant].max()) if relevant.any() else 0.0,
        },
        thresholds={"warn_deg": warn_deg, "fail_deg": fail_deg},
        convention="angle from vertical, build +Z; first-layer band excluded",
    )
