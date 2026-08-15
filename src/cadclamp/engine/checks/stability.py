from __future__ import annotations

import math

import numpy as np
import trimesh
from scipy.spatial import ConvexHull
from shapely.geometry import Point, Polygon

from cadclamp.engine.types import FAIL, PASS, WARN, CheckResult

CONTACT_BAND_MM = 0.3


def check_stability(
    mesh: trimesh.Trimesh,
    *,
    gamma_small_deg: float = 5.0,
    gamma_large_deg: float = 10.0,
    width_cutoff_mm: float = 30.0,
) -> CheckResult:
    """Toppling margin on the build plate, as a continuous tip angle.

    WillItPrint's validated rule: the center of mass must project inside the
    bed-contact hull with safety angle gamma (5 deg for parts <= 30 mm wide,
    10 deg above). We report the actual tip angle rather than a boolean.
    """
    z_min = float(mesh.bounds[0][2])
    contact = mesh.vertices[mesh.vertices[:, 2] < z_min + CONTACT_BAND_MM][:, :2]
    width = float(max(mesh.extents[0], mesh.extents[1]))
    gamma = gamma_small_deg if width <= width_cutoff_mm else gamma_large_deg
    thresholds = {"gamma_deg": gamma, "width_mm": width}

    if len(contact) < 3:
        return CheckResult(
            check="stability",
            index=0.0,
            band=FAIL,
            measured={"reason": "fewer than 3 bed-contact points", "contact_points": int(len(contact))},
            thresholds=thresholds,
        )

    hull = ConvexHull(contact)
    footprint = Polygon(contact[hull.vertices])
    com = mesh.center_mass
    com_xy = Point(float(com[0]), float(com[1]))
    height = max(float(com[2]) - z_min, 1e-9)

    distance = footprint.exterior.distance(com_xy)
    margin = distance if footprint.contains(com_xy) else -distance
    tip_deg = math.degrees(math.atan2(margin, height))

    z = (tip_deg - gamma) / (gamma / 3.0)
    index = 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, z))))
    if tip_deg < gamma * 0.5:
        band = FAIL
    elif tip_deg < gamma:
        band = WARN
    else:
        band = PASS

    return CheckResult(
        check="stability",
        index=index,
        band=band,
        measured={
            "tip_angle_deg": tip_deg,
            "margin_mm": float(margin),
            "com_height_mm": height,
            "footprint_area_mm2": float(footprint.area),
        },
        thresholds=thresholds,
        convention="tip angle = atan2(CoM margin inside bed-contact hull, CoM height)",
    )
