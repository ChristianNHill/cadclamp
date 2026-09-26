import pytest

from cadclamp.engine.composite import two_tier_index, weighted_geometric_mean
from cadclamp.engine.score import score_mesh


def test_two_tier_index_shape():
    assert two_tier_index(0.2, 0.45, 0.8) < 0.05
    assert two_tier_index(1.5, 0.45, 0.8) > 0.95
    mid = two_tier_index(0.625, 0.45, 0.8)
    assert 0.4 < mid < 0.6
    with pytest.raises(ValueError):
        two_tier_index(1.0, 0.8, 0.8)


def test_geometric_mean_tanks_on_one_bad_index():
    good = weighted_geometric_mean({"a": 0.9, "b": 0.9, "c": 0.9})
    bad = weighted_geometric_mean({"a": 0.9, "b": 0.9, "c": 0.01})
    assert good > 0.85
    assert bad < 0.35


def test_good_cube_scores_high(good_cube):
    card = score_mesh(good_cube, part="cube")
    assert not card.gated_out
    assert card.printability > 0.8
    assert len(card.checks) == 3


def test_fail_band_caps_composite(mushroom):
    card = score_mesh(mushroom, part="mushroom")
    assert not card.gated_out
    overhang = next(c for c in card.checks if c.check == "overhang")
    assert overhang.band == "fail"
    # a hard overhang fail must not read as a near-perfect part
    assert card.printability <= 0.5


def test_repairable_soup_scores(open_soup):
    # a benign hole is closed and the part is scored, not zeroed
    card = score_mesh(open_soup, part="soup")
    assert not card.gated_out
    assert card.printability > 0.0
    assert card.checks


def test_nonmanifold_gated_out(nonmanifold):
    card = score_mesh(nonmanifold, part="nm")
    assert card.gated_out
    assert card.failure_code in ("not_watertight", "bad_winding")
    assert card.printability == 0.0
    assert card.checks == []


def test_report_card_serializes(good_cube):
    card = score_mesh(good_cube)
    payload = card.to_json()
    assert "printability" in payload
    assert "min_wall" in payload


def test_interface_assertions_find_holes_and_teeth():
    # empty_cylinder / solid_points / radial_count check where material is,
    # which bbox, volume and Euler number cannot see (Track C interfaces)
    import numpy as np
    import trimesh

    from cadclamp.prompts import check_assertions

    washer = trimesh.creation.annulus(r_min=5.0, r_max=8.0, height=5.0)  # 10 mm bore, z -2.5..2.5
    ok_bore = {"type": "empty_cylinder", "center": [0, 0, 0], "axis": "z", "diameter": 10.0, "length": 5.0}
    too_big = {"type": "empty_cylinder", "center": [0, 0, 0], "axis": "z", "diameter": 12.0, "length": 5.0}
    wall = {"type": "solid_points", "points": [[6.5, 0, 0], [0, -6.5, 0]]}
    res = check_assertions(washer, [ok_bore, too_big, wall])
    assert [r["passed"] for r in res] == [True, False, True]

    teeth = trimesh.util.concatenate([
        trimesh.creation.box([2, 2, 4], transform=trimesh.transformations.rotation_matrix(t, [0, 0, 1])
                             @ trimesh.transformations.translation_matrix([10, 0, 0]))
        for t in np.linspace(0, 2 * np.pi, 20, endpoint=False)])
    count = check_assertions(teeth, [{"type": "radial_count", "center": [0, 0, 0], "axis": "z", "radius": 10.0, "count": 20}])
    assert count[0]["passed"], count[0]


def test_empty_mesh_fails_every_assertion_without_crashing():
    import trimesh

    from cadclamp.prompts import check_assertions

    results = check_assertions(trimesh.Trimesh(), [{"type": "bbox_mm", "min": [1, 1, 1], "max": [2, 2, 2]}, {"type": "watertight"}])
    assert [r["passed"] for r in results] == [False, False]
