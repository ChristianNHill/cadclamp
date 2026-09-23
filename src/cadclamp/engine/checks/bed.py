from __future__ import annotations

import numpy as np
import trimesh

from cadclamp.engine.checks.bridge import _layer_polygon
from cadclamp.engine.composite import two_tier_index
from cadclamp.engine.types import FAIL, PASS, WARN, CheckResult

# Hubs: parts with a large flat footprint lift at the corners and flare at the
# first layer ("elephant's foot"); put a 45 degree chamfer or radius on the
# edges that touch the plate. Craftcloud flags warping risk from ~140 mm; the
# WillItPrint footprint constant is 75 mm. 100 mm is the middle of that range.
LARGE_FOOTPRINT_MM = 100.0
# A chamfer or radius shows up as the first layer sitting inside the layers
# above it. One nozzle width of inset is a real chamfer; a tenth is noise.
RECOMMENDED_INSET_MM = 0.4
FEASIBLE_INSET_MM = 0.1
PROBE_ABOVE_MM = 1.2  # above any bottom chamfer of sensible size


def _inset(first, above, ceiling: float) -> float:
    """How far the first layer's edges sit inside the edges above them.

    first.buffer(d) must cover `above`; the smallest such d is the inset. An
    unchamfered part gives 0. Holes count too: a chamfered hole is wider at
    the plate, and growing `first` closes it toward `above`'s smaller hole.
    """
    if first is None or above is None:
        return 0.0
    if first.contains(above):
        return 0.0
    lo, hi = 0.0, ceiling
    for _ in range(12):
        mid = (lo + hi) / 2.0
        if first.buffer(mid).contains(above):
            hi = mid
        else:
            lo = mid
    return hi


def check_bed_interface(mesh: trimesh.Trimesh, *, layer_mm: float = 0.2) -> CheckResult:
    """Bottom-edge treatment on parts with a large footprint.

    Small parts pass outright: nothing about their bed interface needs
    designing. Past LARGE_FOOTPRINT_MM the first layer is expected to sit
    inside the layers above it (a chamfer or radius on the plate edges), which
    is what limits elephant's foot and gives corners less to lift with.
    """
    z_min = float(mesh.bounds[0][2])
    footprint = float(max(mesh.extents[0], mesh.extents[1]))
    thresholds = {
        "large_footprint_mm": LARGE_FOOTPRINT_MM,
        "recommended_inset_mm": RECOMMENDED_INSET_MM,
        "feasible_inset_mm": FEASIBLE_INSET_MM,
    }
    first = _layer_polygon(mesh, z_min + layer_mm / 2.0)
    contact_area = float(first.area) if first is not None else 0.0
    if footprint <= LARGE_FOOTPRINT_MM:
        return CheckResult(
            check="bed_interface",
            index=1.0,
            band=PASS,
            measured={"footprint_mm": footprint, "contact_area_mm2": contact_area, "reason": "small footprint: no treatment needed"},
            thresholds=thresholds,
        )

    above = _layer_polygon(mesh, z_min + PROBE_ABOVE_MM)
    inset = _inset(first, above, ceiling=5.0)
    index = two_tier_index(inset, FEASIBLE_INSET_MM, RECOMMENDED_INSET_MM)
    if inset >= RECOMMENDED_INSET_MM:
        band = PASS
    elif inset >= FEASIBLE_INSET_MM:
        band = WARN
    else:
        band = FAIL
    return CheckResult(
        check="bed_interface",
        index=index,
        band=band,
        measured={"footprint_mm": footprint, "contact_area_mm2": contact_area, "bottom_edge_inset_mm": inset},
        thresholds=thresholds,
        convention=f"inset of the first layer's outline inside the outline {PROBE_ABOVE_MM} mm above it; only judged past {LARGE_FOOTPRINT_MM:g} mm footprint",
    )
