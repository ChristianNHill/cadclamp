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
