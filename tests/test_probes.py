"""Spec probes (prompts.check_assertions): each one passes the part it
describes and fails the obvious wrong part. v0.2's spec was bbox + volume band
+ euler + body count, which a ball-joint socket with no socket passed."""

import os

import numpy as np
import pytest
import trimesh

from cadclamp.engine.gates import orient_outward
from cadclamp.prompts import check_assertions


def _passed(mesh, *assertions):
    return [r["passed"] for r in check_assertions(mesh, list(assertions))]


def _socket(cavity: bool = True):
    """20 mm cube with a 12 mm spherical void at its centre (sealed)."""
    block = trimesh.creation.box([20, 20, 20])
    if not cavity:
        return block
    return block.difference(trimesh.creation.icosphere(subdivisions=4, radius=6.0), engine="manifold")


def _plate_with_hole(d: float, axis: str = "z"):
    plate = trimesh.creation.box([30, 30, 10 if axis == "z" else 20])
    rot = {"z": np.eye(4), "x": trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])}[axis]
    return plate.difference(trimesh.creation.cylinder(radius=d / 2, height=40, sections=64, transform=rot), engine="manifold")


def test_sealed_void_counts_as_cavity_not_body():
    sphere = {"type": "empty_sphere", "center": [0, 0, 0], "diameter": 12.0}
    counts = [{"type": "cavity_count", "value": 1}, {"type": "body_count", "value": 1}]
    assert _passed(_socket(), sphere, *counts) == [True, True, True]
    assert _passed(_socket(cavity=False), sphere, *counts) == [False, False, True]


def test_orient_outward_keeps_voids_but_fixes_inside_out_solids():
    part = orient_outward(_socket())
    assert part.volume == pytest.approx(20**3 - 4 / 3 * np.pi * 6**3, rel=0.01)
    inside_out = trimesh.creation.box([10, 10, 10])
    inside_out.invert()
    assert orient_outward(inside_out).volume > 0


def test_hole_checks_diameter_from_both_sides():
    plate = _plate_with_hole(10.0)
    probe = {"type": "hole", "center": [0, 0, 0], "axis": "z", "length": 10.0}
    assert _passed(plate, {**probe, "diameter": 10.0}, {**probe, "diameter": 8.0}, {**probe, "diameter": 12.0}) == [True, False, False]
    # empty_cylinder alone cannot see an oversized hole
    assert _passed(plate, {"type": "empty_cylinder", "center": [0, 0, 0], "axis": "z", "diameter": 8.0, "length": 10.0}) == [True]


def test_horizontal_hole_allows_a_teardrop_roof():
    plate = _plate_with_hole(10.0, axis="x")
    roof = trimesh.creation.box([40, 5, 5], transform=trimesh.transformations.compose_matrix(
        angles=[np.pi / 4, 0, 0], translate=[0, 0, 2.5]))
    teardrop = plate.difference(roof, engine="manifold")
    assert _passed(teardrop, {"type": "hole", "center": [0, 0, 0], "axis": "x", "diameter": 10.0, "length": 30.0}) == [True]


def test_box_probes():
    tray = trimesh.creation.box([40, 40, 10]).difference(
        trimesh.creation.box([36, 36, 10], transform=trimesh.transformations.translation_matrix([0, 0, 2])), engine="manifold")
    pocket = {"type": "empty_box", "center": [0, 0, 2], "size": [36, 36, 6]}
    floor = {"type": "solid_box", "center": [0, 0, -4], "size": [36, 36, 2]}
    assert _passed(tray, pocket, floor) == [True, True]
    assert _passed(trimesh.creation.box([40, 40, 10]), pocket, floor) == [False, True]


def test_section_counts_regions_and_holes():
    plate = _plate_with_hole(10.0)
    sec = check_assertions(plate, [{"type": "section", "z": 0.0, "regions": 1, "holes": 1,
                                    "area": {"min": 800, "max": 830}}])[0]
    assert sec["passed"], sec["measured"]
    assert sec["measured"]["area_mm2"] == pytest.approx(900 - np.pi * 25, rel=0.01)


def test_line_count_and_chord():
    fins = trimesh.util.concatenate([
        trimesh.creation.box([2, 20, 10], transform=trimesh.transformations.translation_matrix([x, 0, 0]))
        for x in (-8, -4, 0, 4, 8)])
    assert _passed(fins, {"type": "line_count", "start": [-15, 0, 0], "end": [15, 0, 0], "count": 5}) == [True]
    plate = trimesh.creation.box([30, 30, 5])
    chord = {"type": "chord", "point": [3, 3, 0], "direction": [0, 0, 1]}
    assert _passed(plate, {**chord, "min": 4.9, "max": 5.1}, {**chord, "min": 6.0}) == [True, False]


@pytest.mark.skipif(not os.environ.get("CADCLAMP_OPENSCAD"), reason="OpenSCAD not configured")
def test_reference_iou_scores_the_reference_one(tmp_path):
    (tmp_path / "r.scad").write_text("cube([60, 40, 5]);")
    ref = {"type": "reference_iou", "min": 0.99, "reference": str(tmp_path / "r.scad")}
    exact = trimesh.creation.box([60, 40, 5], transform=trimesh.transformations.translation_matrix([30, 20, 2.5]))
    shorter = trimesh.creation.box([50, 40, 5], transform=trimesh.transformations.translation_matrix([25, 20, 2.5]))
    assert _passed(exact, ref) == [True]
    iou = check_assertions(shorter, [ref])[0]
    assert iou["passed"] is False and iou["measured"]["iou"] == pytest.approx(50 / 60, abs=0.01)


@pytest.mark.skipif(not os.environ.get("CADCLAMP_OPENSCAD"), reason="OpenSCAD not configured")
def test_placement_is_not_graded_but_orientation_is(tmp_path):
    # a valid part in the wrong place passes (probes are re-seated onto the
    # reference's placement); upside down is still wrong: it prints differently
    (tmp_path / "r.scad").write_text(
        "difference() { translate([-15, -15, 0]) cube([30, 30, 10]); translate([0, 0, 5]) cylinder(d = 12, h = 6, $fn = 64); }")
    pocket = {"type": "hole", "center": [0, 0, 8], "axis": "z", "diameter": 12.0, "length": 3.0, "reference": str(tmp_path / "r.scad")}
    part = trimesh.creation.box([30, 30, 10], transform=trimesh.transformations.translation_matrix([0, 0, 5])).difference(
        trimesh.creation.cylinder(radius=6, height=6, sections=64, transform=trimesh.transformations.translation_matrix([0, 0, 8])),
        engine="manifold")
    assert _passed(part, pocket) == [True]
    moved = part.copy().apply_translation([40, -25, -5])
    res = check_assertions(moved, [pocket])[0]
    assert res["passed"] and res["measured"]["seated_mm"] == [-40.0, 25.0, 5.0]
    flipped = part.copy().apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    assert _passed(flipped, pocket) == [False]


@pytest.mark.skipif(not os.environ.get("CADCLAMP_OPENSCAD"), reason="OpenSCAD not configured")
def test_aligned_reference_iou_ignores_orientation_but_not_shape(tmp_path):
    (tmp_path / "r.scad").write_text("difference() { cube([40, 10, 6]); translate([30, 5, -1]) cylinder(d = 4, h = 8, $fn = 48); }")
    probe = {"type": "reference_iou", "min": 0.97, "align": True, "reference": str(tmp_path / "r.scad")}
    part = trimesh.creation.box([40, 10, 6]).difference(
        trimesh.creation.cylinder(radius=2, height=8, sections=48, transform=trimesh.transformations.translation_matrix([10, 0, 0])),
        engine="manifold")
    stood_up = part.copy().apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    no_hole = trimesh.creation.box([40, 10, 6])
    mirrored = part.copy().apply_transform(np.diag([1, -1, 1, 1]))  # same here: symmetric in Y
    assert _passed(stood_up, probe) == [True]
    assert _passed(mirrored, probe) == [True]
    assert check_assertions(no_hole, [probe])[0]["measured"]["iou"] < 0.97


def _twisted(profile: str, twist: float, height: float = 20.0) -> trimesh.Trimesh:
    from cadclamp.mutants import render

    return render(f"$fn = 96; linear_extrude(height = {height}, twist = {twist}, slices = 160, convexity = 4) {profile}")


HELIX = {"type": "helix", "center": [0, 0, 0], "radius": 5.0, "z": [2, 18], "pitch": 4.0}


@pytest.mark.skipif(not os.environ.get("CADCLAMP_OPENSCAD"), reason="OpenSCAD not configured")
def test_helix_sees_hand_starts_and_pitch():
    # an off-centre disc swept with twist is a one-start helical lobe; an
    # ellipse is a two-start one. OpenSCAD's positive twist is clockwise seen
    # from +Z, so negative twist rises counter-clockwise: a right-hand helix.
    one = "translate([1, 0]) circle(r = 5);"
    two = "scale([1.25, 0.8]) circle(r = 5);"
    rh1 = _twisted(one, -360 * 20 / 4)       # lead 4 = pitch 4
    lh1 = _twisted(one, 360 * 20 / 4)
    rh2 = _twisted(two, -360 * 20 / 8)       # lead 8, two starts: pitch 4
    right1, right2 = {**HELIX, "hand": "right", "starts": 1}, {**HELIX, "hand": "right", "starts": 2}
    assert _passed(rh1, right1, right2) == [True, False]
    assert _passed(lh1, right1, {**right1, "hand": "left"}) == [False, True]
    assert _passed(rh2, right1, right2) == [False, True]
    measured = check_assertions(rh2, [right2])[0]["measured"]
    assert measured["pitch_mm"] == pytest.approx(4.0, rel=0.05)
    # the same ellipse at lead 4 is a two-start thread of pitch 2
    assert _passed(_twisted(two, -360 * 20 / 4), right2) == [False]


@pytest.mark.skipif(not os.environ.get("CADCLAMP_OPENSCAD"), reason="OpenSCAD not configured")
def test_helix_rejects_stacked_rings():
    from cadclamp.mutants import render

    # V-grooved tube: crests every 4 mm like a thread, but rings, not a helix
    rings = render("$fn = 96; rotate_extrude() polygon(concat([[2, 0]], "
                   "[for (i = [0:10]) each [[6, 4 * i], [4, 4 * i + 2]]], [[6, 44], [2, 44]]));")
    res = check_assertions(rings, [{**HELIX, "hand": "right", "starts": 1}])[0]
    assert res["passed"] is False and res["measured"]["starts"] == 0


@pytest.mark.skipif(not os.environ.get("CADCLAMP_OPENSCAD"), reason="OpenSCAD not configured")
@pytest.mark.parametrize("pid,radius,z,pitch", [
    ("t4-003", 9.23, [8.5, 33.5], 2.5), ("t4-004", 9.525, [5, 16], 2.5),
    ("t4-007", 13.25, [1.2, 13], 4.0), ("t4-007", 11.25, [22, 38], 3.0)])
def test_helix_passes_the_thread_references(pid, radius, z, pitch):
    from cadclamp.mutants import render
    from cadclamp.prompts import PROMPTS_DIR

    ref = render((PROMPTS_DIR / "v0.2" / "reference" / f"{pid}.scad").read_text())
    probe = {"type": "helix", "center": [0, 0, 0], "radius": radius, "z": z, "pitch": pitch, "hand": "right", "starts": 1}
    res = check_assertions(ref, [probe])[0]
    assert res["passed"], res["measured"]
    assert _passed(ref, {**probe, "hand": "left"}, {**probe, "starts": 2}) == [False, False]


def _ball_in_eye(captive: bool):
    """A 10 mm ball in a 20 mm block, 0.5 mm clear all round. The eye is
    open top and bottom: through a 6 mm hole (captive) or a 11 mm one."""
    block = trimesh.creation.box([20, 20, 10])
    seat = trimesh.creation.icosphere(subdivisions=4, radius=5.5)
    hole = trimesh.creation.cylinder(radius=3 if captive else 5.5, height=30, sections=64)
    housing = block.difference(seat, engine="manifold").difference(hole, engine="manifold")
    ball = trimesh.creation.icosphere(subdivisions=4, radius=5.0).intersection(
        trimesh.creation.box([12, 12, 9]), engine="manifold")
    return trimesh.util.concatenate([housing, ball])


def test_captive_and_same_body():
    push = {"type": "captive", "point": [0, 0, 0], "directions": [[0, 0, 1], [0, 0, -1], [1, 0, 0]]}
    owners = {"type": "same_body", "groups": [[[0, 0, 0], [4, 0, 0]], [[9, 0, 0], [-9, 9, 0]]]}
    assert _passed(_ball_in_eye(True), push, owners) == [True, True]
    assert _passed(_ball_in_eye(False), push, owners) == [False, True]
    # the ball and the housing swapped between groups, or one body claimed twice
    assert _passed(_ball_in_eye(True), {**owners, "groups": [[[0, 0, 0], [9, 0, 0]], [[-9, 9, 0]]]}) == [False]
    assert _passed(_ball_in_eye(True), {**owners, "groups": [[[0, 0, 0]], [[4, 0, 0]]]}) == [False]
