from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh

from cadclamp.engine.types import FAIL, PASS, SKIPPED, GateResult

MIN_VOLUME_MM3 = 1e-6


def load_mesh(path: str | Path) -> trimesh.Trimesh:
    mesh = trimesh.load(str(path), force="mesh")
    # STL is unwelded triangle soup; without merging, every manifoldness
    # check fails spuriously on duplicate vertices.
    mesh.merge_vertices()
    return mesh


def gate_degenerate(mesh: trimesh.Trimesh) -> GateResult:
    gate = "G1.degenerate"
    if mesh.is_empty or len(mesh.faces) < 4:
        return GateResult(gate, FAIL, "no_output", {"faces": int(len(mesh.faces))})
    if not np.isfinite(mesh.bounds).all():
        return GateResult(gate, FAIL, "degenerate_volume", {"reason": "non-finite bounds"})
    extents = mesh.extents
    if extents is None or float(np.min(extents)) <= 0.0:
        return GateResult(gate, FAIL, "degenerate_volume", {"reason": "zero extent"})
    volume = float(abs(mesh.volume)) if mesh.is_watertight else None
    if volume is not None and volume < MIN_VOLUME_MM3:
        return GateResult(gate, FAIL, "degenerate_volume", {"volume_mm3": volume})
    return GateResult(gate, PASS, detail={"extents_mm": [float(x) for x in extents]})


def _manifold3d_status(mesh: trimesh.Trimesh) -> str:
    try:
        import manifold3d as m3d

        mm = m3d.Mesh(
            vert_properties=np.asarray(mesh.vertices, dtype=np.float32),
            tri_verts=np.asarray(mesh.faces, dtype=np.uint32),
        )
        man = m3d.Manifold(mm)
        status = man.status
        if callable(status):
            status = status()
        return str(getattr(status, "name", status))
    except Exception as exc:  # independent oracle only; trimesh predicates gate
        return f"unavailable: {exc}"


def gate_valid_solid(mesh: trimesh.Trimesh) -> GateResult:
    gate = "G2.valid_solid"
    detail = {
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "body_count": int(mesh.body_count),
        "euler_number": int(mesh.euler_number),
        "manifold3d_status": _manifold3d_status(mesh),
    }
    if not mesh.is_watertight:
        return GateResult(gate, FAIL, "not_watertight", detail)
    if not mesh.is_winding_consistent:
        return GateResult(gate, FAIL, "bad_winding", detail)
    # is_volume additionally requires finite center_mass and positive volume
    if not mesh.is_volume:
        detail["volume_mm3"] = float(mesh.volume)
        return GateResult(gate, FAIL, "not_a_volume", detail)
    detail["volume_mm3"] = float(mesh.volume)
    return GateResult(gate, PASS, detail=detail)


def gate_self_intersection(mesh: trimesh.Trimesh) -> GateResult:
    gate = "G3.self_intersection"
    try:
        import open3d as o3d
    except ImportError:
        return GateResult(
            gate,
            SKIPPED,
            detail={"reason": "open3d unavailable in this environment; run in the scoring container"},
        )
    om = o3d.geometry.TriangleMesh(
        o3d.utility.Vector3dVector(np.asarray(mesh.vertices)),
        o3d.utility.Vector3iVector(np.asarray(mesh.faces)),
    )
    if om.is_self_intersecting():
        return GateResult(gate, FAIL, "self_intersecting", {})
    return GateResult(gate, PASS)


def run_gates(mesh: trimesh.Trimesh) -> list[GateResult]:
    results: list[GateResult] = []
    for fn in (gate_degenerate, gate_valid_solid, gate_self_intersection):
        result = fn(mesh)
        results.append(result)
        if result.status == FAIL:
            break
    return results
