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
