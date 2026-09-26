"""OrcaSlicer sidecar: G-code accounting (pure) and a real slice per machine
(skipped when OrcaSlicer is not installed)."""

import os

import pytest
import trimesh

from cadclamp.slicer.orca import MACHINES, ORCA, extrusion_by_feature, slice_part


def test_extrusion_is_attributed_to_features_in_both_extrusion_modes():
    gcode = "\n".join([
        "M82", "G92 E0",
        "; FEATURE: Outer wall", "G1 X1 E1.0", "G1 X2 E2.5",
        ";TYPE:Support", "G1 X3 E3.0", "G1 E2.0 ; retract", "G1 E3.0 ; unretract", "G1 X4 E3.5",
        "M83", "; FEATURE: Sparse infill", "G1 X5 E0.4", "G1 E-0.8",
    ])
    per = extrusion_by_feature(gcode)
    assert per["Outer wall"] == pytest.approx(2.5)
    assert per["Support"] == pytest.approx(1.0)  # the unretract is not extrusion
    assert per["Sparse infill"] == pytest.approx(0.4)


@pytest.mark.skipif(not os.path.exists(ORCA), reason="OrcaSlicer not installed")
@pytest.mark.parametrize("machine", sorted(MACHINES))
def test_real_slicer_sees_the_overhang(machine, tmp_path):
    cube = trimesh.creation.box([20, 20, 20])
    cube.apply_translation([0, 0, 10])
    stem = trimesh.creation.box([8, 8, 20])
    stem.apply_translation([0, 0, 10])
    cap = trimesh.creation.box([40, 40, 4])
    cap.apply_translation([0, 0, 22])
    cube.export(tmp_path / "cube.stl")
    trimesh.util.concatenate([stem, cap]).export(tmp_path / "mushroom.stl")

    plain = slice_part(tmp_path / "cube.stl", machine)
    mushroom = slice_part(tmp_path / "mushroom.stl", machine)
    assert plain["sliced"] and mushroom["sliced"]
    assert plain["support_mm"] == 0
    assert mushroom["support_fraction"] > 0.3
