from __future__ import annotations

import trimesh

from cadclamp.engine.checks.wall import check_min_wall
from cadclamp.engine.composite import two_tier_index
from cadclamp.engine.types import FAIL, PASS, WARN, CheckResult

# Hubs living-hinge guide for FDM: web 0.3-0.8 mm thick (0.4-0.6 typical).
# Thinner does not print; thicker does not flex and cracks along the layer.
MIN_HINGE_MM = 0.3
MAX_HINGE_MM = 0.8


def check_living_hinge(mesh: trimesh.Trimesh, *, line_width_mm: float = 0.4) -> CheckResult:
    """The one place a thin wall is the requirement, not the defect.

    Reads the thinnest robust wall from the min-wall measurement and asks that
    it fall inside the living-hinge band. min_wall still runs on the same
    part and will warn about the web; this column is the counterweight that
    says the web is what was asked for.
    """
    wall = check_min_wall(mesh, line_width_mm=line_width_mm)
    thin = wall.measured.get("thin_wall_p2_mm")
    thresholds = {"min_mm": MIN_HINGE_MM, "max_mm": MAX_HINGE_MM}
    if thin is None:
        return CheckResult(check="living_hinge", index=0.0, band=FAIL, measured=wall.measured, thresholds=thresholds)
    # inside the band both factors sit near 1; each shoulder falls away over ~0.15 mm
    index = two_tier_index(thin, MIN_HINGE_MM - 0.15, MIN_HINGE_MM) * two_tier_index(-thin, -(MAX_HINGE_MM + 0.4), -MAX_HINGE_MM)
    if MIN_HINGE_MM <= thin <= MAX_HINGE_MM:
        band = PASS
    elif MIN_HINGE_MM - 0.1 <= thin <= MAX_HINGE_MM + 0.4:
        band = WARN
    else:
        band = FAIL
    return CheckResult(
        check="living_hinge",
        index=index,
        band=band,
        measured={"hinge_web_mm": thin},
        thresholds=thresholds,
        convention="thinnest robust wall (min_wall p2) must lie inside the living-hinge band",
    )
