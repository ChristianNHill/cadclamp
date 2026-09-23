from __future__ import annotations

import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union

from cadclamp.engine.composite import two_tier_index
from cadclamp.engine.types import FAIL, PASS, WARN, CheckResult

# Measured as REACH: the furthest an unsupported region gets from material
# underneath. A two-sided bridge of span S has reach S/2, because the
# extruder anchors on both ends; a cantilever of length L has reach L and is
# the worse case. Reporting reach grades both with one number, where a
# doubled "span" would libel a cantilever as twice its own length.
# Hubs/Protolabs FDM guidance: spans under 5 mm bridge with no visible sag,
# and past ~20 mm a designer should expect support or a chamfered roof.
RECOMMENDED_REACH_MM = 2.5  # = a 5 mm two-sided bridge
FEASIBLE_REACH_MM = 10.0  # = a 20 mm two-sided bridge

# Tessellation slivers on curved undersides are overhangs, not bridges; the
# overhang check already grades them. Ignore unsupported patches below this.
MIN_PATCH_AREA_MM2 = 1.0

# Scanning is a geometric measurement, not a print simulation, so it does not
# need real layer resolution. Cap the section count to keep tall parts cheap.
MAX_SCAN_LAYERS = 120


def _layer_polygon(mesh: trimesh.Trimesh, z: float):
    """Solid cross-section at height z, as one shapely geometry (None if empty)."""
    section = mesh.section(plane_origin=[0.0, 0.0, z], plane_normal=[0.0, 0.0, 1.0])
    if section is None:
        return None
    try:
        planar, _ = section.to_2D(to_2D=np.eye(4))
    except Exception:
        return None
    polygons = [p for p in planar.polygons_full if p.is_valid and not p.is_empty]
    if not polygons:
        return None
    return unary_union(polygons)


def _reach_over(patch, support, ceiling: float) -> float:
    """Furthest any point of `patch` sits from supporting material.

    Found by bisecting the buffer radius that first swallows the patch, which
    is cheaper and steadier than building a medial axis.
    """
    if support is None or support.is_empty:
        return ceiling  # a floating island: nothing under it anywhere
    lo, hi = 0.0, ceiling
    if not support.buffer(hi).contains(patch):
        return ceiling
    for _ in range(12):
        mid = (lo + hi) / 2.0
        if support.buffer(mid).contains(patch):
            hi = mid
        else:
            lo = mid
    return hi


def check_bridge(
    mesh: trimesh.Trimesh,
    *,
    layer_mm: float = 0.2,
    recommended_mm: float = RECOMMENDED_REACH_MM,
    feasible_mm: float = FEASIBLE_REACH_MM,
) -> CheckResult:
    """Longest unsupported horizontal span the part asks the printer to bridge.

    Per layer, material that is not over the layer below (grown by one layer
    of 45 degree reach, the Langelaar filter) is unsupported; the measure is
    how far that region reaches from the nearest material underneath. A flat
    roof over a hole gives one wide region and a long reach; a 45 degree
    pointed roof over the same hole is supported layer by layer and reaches
    nothing, which is the design difference this check exists to separate.

    Convention: build direction +Z, reach measured in the layer plane, bed
    contact excluded (the first layer is supported by the plate).
    """
    z_min, z_max = float(mesh.bounds[0][2]), float(mesh.bounds[1][2])
    height = z_max - z_min
    thresholds = {
        "recommended_mm": recommended_mm,
        "feasible_mm": feasible_mm,
        "layer_mm": layer_mm,
    }
    if height <= 2 * layer_mm:
        return CheckResult(
            check="bridge_span",
            index=1.0,
            band=PASS,
            measured={"max_reach_mm": 0.0, "reason": "part is a single layer"},
            thresholds=thresholds,
        )

    step = max(layer_mm, height / MAX_SCAN_LAYERS)
    ceiling = float(np.linalg.norm(mesh.extents[:2]))  # no span can exceed the footprint diagonal
    worst_reach, worst_z, worst_area = 0.0, None, 0.0

    below = _layer_polygon(mesh, z_min + step / 2.0)
    z = z_min + 1.5 * step
    while z < z_max:
        here = _layer_polygon(mesh, z)
        if here is not None:
            # one layer of 45 degree reach is what the previous layer can carry
            supported = below.buffer(step) if below is not None else None
            unsupported = here if supported is None else here.difference(supported)
            if not unsupported.is_empty:
                patches = getattr(unsupported, "geoms", [unsupported])
                for patch in patches:
                    if patch.area < MIN_PATCH_AREA_MM2:
                        continue
                    reach = _reach_over(patch, below, ceiling)
                    if reach > worst_reach:
                        worst_reach, worst_z, worst_area = reach, z, patch.area
        below = here
        z += step

    # nothing unsupported anywhere is a clean 1.0, not the logistic's asymptote
    index = 1.0 if worst_reach == 0.0 else two_tier_index(-worst_reach, -feasible_mm, -recommended_mm)
    if worst_reach <= recommended_mm:
        band = PASS
    elif worst_reach <= feasible_mm:
        band = WARN
    else:
        band = FAIL

    return CheckResult(
        check="bridge_span",
        index=index,
        band=band,
        measured={
            "max_reach_mm": worst_reach,
            # what the same reach means as a bridge anchored at both ends,
            # for comparison with published span limits
            "equivalent_two_sided_span_mm": 2.0 * worst_reach,
            "at_z_mm": worst_z,
            "patch_area_mm2": worst_area,
            "scan_step_mm": step,
        },
        thresholds=thresholds,
        convention="unsupported layer region vs the layer below grown by 45 deg; reach = furthest distance from support",
    )
