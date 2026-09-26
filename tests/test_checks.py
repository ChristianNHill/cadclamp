from cadclamp.engine.checks import check_min_wall, check_overhang, check_stability
from cadclamp.engine.types import FAIL, PASS


def test_cube_wall_thick(good_cube):
    result = check_min_wall(good_cube)
    assert result.band == PASS
    assert result.index > 0.9
    assert result.measured["median_mm"] > 5.0


def test_thin_wall_box_flagged(thin_wall_box):
    result = check_min_wall(thin_wall_box)
    assert result.band != PASS
    assert result.measured["thin_wall_p2_mm"] < 0.8


def test_cube_overhang_clean(good_cube):
    result = check_overhang(good_cube)
    assert result.band == PASS
    assert result.measured["fail_area_fraction"] == 0.0


def test_mushroom_overhang_fails(mushroom):
    result = check_overhang(mushroom)
    assert result.band == FAIL
    assert result.measured["fail_area_fraction"] > 0.05
    assert result.measured["max_overhang_deg"] > 85


def test_cube_stable(good_cube):
    result = check_stability(good_cube)
    assert result.band == PASS
    assert result.measured["tip_angle_deg"] > 30


def test_tall_pin_unstable(tall_pin):
    result = check_stability(tall_pin)
    assert result.band == FAIL
    assert result.measured["tip_angle_deg"] < 2.5


def test_stability_fails_a_part_resting_on_an_edge():
    # a triangular prism standing on one edge touches the bed along a line;
    # Qhull cannot build a 2-D hull from collinear points (a gpt-5.1 Fusion
    # part crashed the whole eval this way), so it must score as a FAIL
    import trimesh

    corners = [[x, y, z] for x in (0, 30) for y, z in ((0, 0), (-10, 20), (10, 20))]
    prism = trimesh.convex.convex_hull(corners)
    result = check_stability(prism)
    assert result.band == FAIL
    assert result.index == 0.0
