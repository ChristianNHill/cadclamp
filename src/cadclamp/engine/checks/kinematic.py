from __future__ import annotations

import numpy as np
import trimesh

from cadclamp.engine.types import FAIL, PASS, WARN, CheckResult

ROTATION_STEPS = 8  # every 45 degrees about the assembly axis
CAPTIVE_TRAVEL_MM = 3.0  # pushing the moving body this far along the axis must hit something
INTERFERENCE_MM3 = 0.01  # boolean noise floor


def _interferes(a: trimesh.Trimesh, b: trimesh.Trimesh) -> float:
    try:
        hit = a.intersection(b, engine="manifold")
    except Exception:
        return float("inf")
    return float(abs(hit.volume)) if hit is not None and not hit.is_empty else 0.0


def check_kinematic_sweep(mesh: trimesh.Trimesh) -> CheckResult:
    """Does a print-in-place joint actually move, and does it stay together?

    Convention: the joint axis is Z through the assembly's XY centre (the
    print-in-place prompts state it). The body with the smaller radial reach
    is the moving one. It is turned through a full revolution in steps and
    must never intersect the other body; then it is pushed along the axis both
    ways and must collide, or the parts fall apart once printed.
    """
    bodies = mesh.split(only_watertight=False)
    thresholds = {"rotation_steps": ROTATION_STEPS, "captive_travel_mm": CAPTIVE_TRAVEL_MM}
    if len(bodies) != 2:
        return CheckResult(
            check="kinematic_sweep",
            index=0.0,
            band=FAIL,
            measured={"body_count": int(len(bodies)), "reason": "needs exactly two bodies"},
            thresholds=thresholds,
        )
    centre = mesh.bounds.mean(axis=0)
    centre[2] = 0.0
    reach = [float(np.max(np.linalg.norm((b.vertices - centre)[:, :2], axis=1))) for b in bodies]
    moving, fixed = (bodies[0], bodies[1]) if reach[0] <= reach[1] else (bodies[1], bodies[0])

    worst = 0.0
    for k in range(ROTATION_STEPS):
        turned = moving.copy()
        turned.apply_transform(trimesh.transformations.rotation_matrix(2 * np.pi * k / ROTATION_STEPS, [0, 0, 1], centre))
        worst = max(worst, _interferes(turned, fixed))
    free = worst <= INTERFERENCE_MM3

    captive = True
    for direction in (1.0, -1.0):
        pushed = moving.copy()
        pushed.apply_translation([0, 0, direction * CAPTIVE_TRAVEL_MM])
        if _interferes(pushed, fixed) <= INTERFERENCE_MM3:
            captive = False

    if free and captive:
        index, band = 1.0, PASS
    elif free:
        index, band = 0.5, WARN  # turns, but nothing keeps it on: it falls apart
    else:
        index, band = 0.0, FAIL  # the bodies interfere: it prints as one lump
    return CheckResult(
        check="kinematic_sweep",
        index=index,
        band=band,
        measured={"max_interference_mm3": worst, "turns_freely": free, "captive": captive},
        thresholds=thresholds,
        convention="moving body = smaller radial reach; full turn about Z in steps must not intersect; axial push both ways must collide",
    )
