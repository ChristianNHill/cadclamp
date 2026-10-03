import os
import subprocess

import numpy as np
import pytest
import trimesh

from cadclamp.engine.gates import gate_degenerate, gate_valid_solid, run_gates
from cadclamp.engine.types import FAIL, PASS


def test_good_cube_passes_gates(good_cube):
    results = run_gates(good_cube)
    hard = [g for g in results if g.status == FAIL]
    assert hard == []
    assert results[0].status == PASS
    assert results[1].status == PASS


def test_open_soup_is_repaired(open_soup):
    # two missing faces are simple holes; light repair closes them
    result = gate_valid_solid(open_soup)
    assert result.status == PASS
    assert result.code == "repaired" or result.detail.get("repaired")


def test_nonmanifold_fails_but_is_slicer_recoverable(nonmanifold):
    result = gate_valid_solid(nonmanifold)
    assert result.status == FAIL
    assert result.code in ("not_watertight", "bad_winding")
    assert result.detail.get("slicer_recoverable") is True


def test_empty_mesh_is_degenerate():
    empty = trimesh.Trimesh()
    result = gate_degenerate(empty)
    assert result.status == FAIL
    assert result.code == "no_output"


def test_gates_stop_at_first_failure(nonmanifold):
    results = run_gates(nonmanifold)
    assert results[-1].status == FAIL
    assert len(results) == 2  # degenerate passed, valid_solid failed, G3 never ran


def test_inside_out_bodies_are_oriented_outward(tmp_path):
    # slicers flip inverted normals, so an inside-out solid is not a defect:
    # six models' OpenSCAD t1-005 wedges failed only on negative volume
    import trimesh

    from cadclamp.engine.gates import load_mesh

    good = trimesh.creation.box([10, 10, 10])
    flipped = trimesh.creation.box([10, 10, 10])
    flipped.apply_translation([20, 0, 0])
    flipped.invert()
    path = tmp_path / "two.stl"
    trimesh.util.concatenate([good, flipped]).export(path)
    mesh = load_mesh(path)
    assert abs(mesh.volume - 2000.0) < 1e-6
    assert all(b.volume > 0 for b in mesh.split(only_watertight=False))


def test_closed_surface_with_touching_bodies_is_slicer_recoverable():
    # two boxes sharing one edge: no open edges, but that edge has four faces
    # (the 3DBenchy defect); slicers print it, so it is tagged recoverable
    a = trimesh.creation.box(extents=(10, 10, 10))
    b = trimesh.creation.box(extents=(10, 10, 10))
    b.apply_translation((10, 10, 0))
    mesh = trimesh.util.concatenate([a, b])
    mesh.merge_vertices()
    result = gate_valid_solid(mesh)
    assert result.status == FAIL
    assert result.detail["open_edges"] == 0
    assert result.detail["touching_edges"] > 0
    assert result.detail["slicer_recoverable"] is True


def test_cli_notes_slicer_recoverable_parts(tmp_path, capsys):
    from cadclamp.cli import main

    a = trimesh.creation.box(extents=(10, 10, 10))
    b = trimesh.creation.box(extents=(10, 10, 10))
    b.apply_translation((10, 10, 0))
    mesh = trimesh.util.concatenate([a, b])
    mesh.merge_vertices()
    path = tmp_path / "touching.stl"
    mesh.export(path)
    main(["score", str(path)])
    out = capsys.readouterr().out
    assert "FAIL:not_watertight*" in out
    assert "slicers should still print it" in out


def _pole_sliver(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    # OCCT's sphere pole: one face split off as a sliver whose two pole
    # vertices are separate copies at the same point
    v, f = mesh.vertices, mesh.faces
    a, b, _ = f[0]
    pole = len(v)
    vertices = np.vstack([v, v[a]])
    faces = np.vstack([f, [[a, pole, b]]])
    return trimesh.Trimesh(vertices=vertices, faces=faces, process=False)


def test_pole_sliver_does_not_open_the_solid(tmp_path):
    from cadclamp.engine.gates import load_mesh

    path = tmp_path / "pole.stl"
    _pole_sliver(trimesh.creation.box(extents=(10, 10, 10))).export(path)
    mesh = load_mesh(path)
    assert mesh.is_watertight
    assert abs(mesh.volume - 1000.0) < 1e-6


def test_deleted_face_still_open(tmp_path, open_soup):
    from cadclamp.engine.gates import load_mesh

    path = tmp_path / "open.stl"
    _pole_sliver(open_soup).export(path)
    assert not load_mesh(path).is_watertight


def test_bodies_touching_along_an_edge_stay_non_manifold(tmp_path):
    from cadclamp.engine.gates import load_mesh

    a = trimesh.creation.box(extents=(10, 10, 10))
    b = trimesh.creation.box(extents=(10, 10, 10))
    b.apply_translation((10, 10, 0))
    path = tmp_path / "touching.stl"
    _pole_sliver(trimesh.util.concatenate([a, b])).export(path)
    mesh = load_mesh(path)
    assert not mesh.is_watertight
    assert gate_valid_solid(mesh).detail["touching_edges"] > 0


@pytest.mark.skipif(not os.environ.get("CADCLAMP_SANDBOX_PYTHON"), reason="build123d not configured")
@pytest.mark.parametrize("shape", ["Sphere(10.4)", "Box(30, 30, 30) - Pos(0, 0, 15) * Sphere(10.4)"])
def test_build123d_sphere_is_watertight(tmp_path, shape):
    # every part with a spherical surface failed watertightness before 0.2.3
    from cadclamp.engine.gates import load_mesh

    path = tmp_path / "part.stl"
    code = f"from build123d import *\nexport_stl({shape}, {str(path)!r})\n"
    subprocess.run([os.environ["CADCLAMP_SANDBOX_PYTHON"], "-c", code], check=True)
    mesh = load_mesh(path)
    assert mesh.is_watertight and mesh.is_winding_consistent
