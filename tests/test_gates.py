import trimesh

from cadclamp.engine.gates import gate_degenerate, gate_valid_solid, run_gates
from cadclamp.engine.types import FAIL, PASS


def test_good_cube_passes_gates(good_cube):
    results = run_gates(good_cube)
    hard = [g for g in results if g.status == FAIL]
    assert hard == []
    assert results[0].status == PASS
    assert results[1].status == PASS


def test_open_soup_fails_watertight(open_soup):
    result = gate_valid_solid(open_soup)
    assert result.status == FAIL
    assert result.code == "not_watertight"


def test_empty_mesh_is_degenerate():
    empty = trimesh.Trimesh()
    result = gate_degenerate(empty)
    assert result.status == FAIL
    assert result.code == "no_output"


def test_gates_stop_at_first_failure(open_soup):
    results = run_gates(open_soup)
    assert results[-1].status == FAIL
    assert len(results) == 2  # degenerate passed, valid_solid failed, G3 never ran
