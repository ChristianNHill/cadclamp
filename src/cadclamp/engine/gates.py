from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh

from cadclamp.engine.winding import contains
from cadclamp.engine.types import FAIL, PASS, SKIPPED, GateResult

MIN_VOLUME_MM3 = 1e-6


def load_mesh(path: str | Path) -> trimesh.Trimesh:
    mesh = trimesh.load(str(path), force="mesh")
    # STL is unwelded triangle soup; without merging, every manifoldness
    # check fails spuriously on duplicate vertices.
    mesh.merge_vertices()
    # Merging can collapse a sliver to a face that repeats a vertex: OCCT
    # tessellates a sphere's pole that way. The face has no area, but it
    # leaves one open and one non-manifold edge, so every part with a
    # spherical surface read as not watertight (engine 0.2.3).
    f = mesh.faces
    mesh.update_faces((f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2]))
    return orient_outward(mesh)


def orient_outward(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Flip any closed body whose faces point inward, as every slicer does.

    An inside-out solid (negative signed volume) prints exactly like the
    correct one, so it is not a printability defect: OpenSCAD polyhedra with
    reversed winding and Rhino Breps with Inward orientation produced these.
    Geometry that is wrong because a boolean misfired is untouched.

    A shell nested inside an odd number of other shells is the wall of a
    sealed void, and facing inward is correct for it (engine 0.2.2: 0.2.1
    flipped these too, filling the void with solid).
    """
    bodies = mesh.split(only_watertight=False)
    if not any(b.is_watertight and b.volume < 0 for b in bodies):
        return mesh
    closed = [b for b in bodies if b.is_watertight]
    inward = [i for i, b in enumerate(closed) if b.volume < 0]
    # nesting depth of each inward shell: how many other closed shells hold its
    # first vertex. A bounding-box test rules out almost every pair, and each
    # container is tested once against all its candidates (a failed boolean
    # can leave tens of thousands of fragments; pair by pair took 26 minutes)
    probes = np.array([closed[i].vertices[0] for i in inward])
    position = {i: k for k, i in enumerate(inward)}
    depth = np.zeros(len(inward), dtype=int)
    for j, other in enumerate(closed):
        lo, hi = other.bounds
        cand = np.all((probes >= lo) & (probes <= hi), axis=1)
        if j in position:  # a shell never contains itself
            cand[position[j]] = False
        if cand.any():
            depth[cand] += contains(other, probes[cand])
    for k, i in enumerate(inward):
        if depth[k] % 2 == 0:
            closed[i].invert()
    return trimesh.util.concatenate(bodies)


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


def light_repair(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """The kind of cheap mesh repair a slicer does at load: weld coincident
    vertices, fix winding/normals, fill simple holes. Closes benign export
    artifacts; it does NOT fix non-manifold edges (3+ faces on one edge), which
    is why a part like 3DBenchy stays open under it and only a slicer's per-layer
    approach recovers it."""
    m = mesh.copy()
    try:
        m.merge_vertices()
        m.update_faces(m.nondegenerate_faces())
        m.update_faces(m.unique_faces())
        trimesh.repair.fix_winding(m)
        trimesh.repair.fill_holes(m)
        trimesh.repair.fix_normals(m)
    except Exception:
        pass
    return m


def validate_solid(mesh: trimesh.Trimesh) -> tuple[GateResult, trimesh.Trimesh]:
    """Three-way validity: valid as-is, repaired (score the repaired mesh), or
    not a solid. A non-solid that is still one coherent body is tagged
    slicer_recoverable, because a slicer closes it per-layer at load; that is a
    different thing from degenerate output. Returns the gate result and the mesh
    downstream checks should run on."""
    gate = "G2.valid_solid"
    detail = {
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "body_count": int(mesh.body_count),
        "euler_number": int(mesh.euler_number),
        "manifold3d_status": _manifold3d_status(mesh),
    }
    if mesh.is_watertight and mesh.is_winding_consistent and mesh.is_volume:
        detail["volume_mm3"] = float(mesh.volume)
        return GateResult(gate, PASS, detail=detail), mesh

    repaired = light_repair(mesh)
    if repaired.is_watertight and repaired.is_winding_consistent and repaired.is_volume:
        detail["repaired"] = True
        detail["volume_mm3"] = float(repaired.volume)
        return GateResult(gate, PASS, "repaired", detail), repaired

    # Repair could not close it. Distinguish "a slicer would still print this"
    # from degenerate output: either one coherent body, or a closed surface
    # whose only defect is surfaces touching along edges (no open edges), as
    # in 3DBenchy. Slicers print both; OrcaSlicer checked on real models.
    try:
        hull_volume = float(mesh.convex_hull.volume)
    except Exception:
        hull_volume = 0.0
    counts = np.unique(mesh.edges_sorted, axis=0, return_counts=True)[1] if len(mesh.faces) else np.array([])
    detail["open_edges"] = int((counts == 1).sum())
    detail["touching_edges"] = int((counts > 2).sum())
    closed = detail["open_edges"] == 0
    detail["slicer_recoverable"] = bool(hull_volume > 1.0 and (mesh.body_count == 1 or closed))
    code = "not_watertight" if not mesh.is_watertight else "bad_winding"
    return GateResult(gate, FAIL, code, detail), mesh


def gate_valid_solid(mesh: trimesh.Trimesh) -> GateResult:
    """Verdict only (validity gate); see validate_solid for the mesh-threading form."""
    return validate_solid(mesh)[0]


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
    """Ordered gates, stopping at the first failure. Self-intersection runs on
    the effective (possibly repaired) mesh."""
    results, effective = run_gates_with_mesh(mesh)
    return results


def run_gates_with_mesh(mesh: trimesh.Trimesh) -> tuple[list[GateResult], trimesh.Trimesh]:
    results: list[GateResult] = []
    g1 = gate_degenerate(mesh)
    results.append(g1)
    if g1.status == FAIL:
        return results, mesh
    g2, effective = validate_solid(mesh)
    results.append(g2)
    if g2.status == FAIL:
        return results, effective
    g3 = gate_self_intersection(effective)
    results.append(g3)
    return results, effective
