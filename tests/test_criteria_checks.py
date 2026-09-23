"""Criterion checks: the DfAM rules a prompt opts into via its `criteria:` tag.

Each case is a pair that differs only in the design decision the check exists
to grade, so a check that always returned the same band would fail here.
"""

import trimesh

from cadclamp.engine.checks import check_bridge, check_clearance
from cadclamp.engine.score import score_mesh


def grounded(m):
    m.apply_translation([0, 0, -m.bounds[0][2]])
    return m


def tunnel(roof: str):
    """50 x 20 x 34 block with a 30 mm wide tunnel; flat or 45-degree roof."""
    block = trimesh.creation.box(extents=[50, 20, 34])
    cut = trimesh.creation.box(extents=[30, 22, 10])
    cut.apply_translation([0, 0, -34 / 2 + 4 + 5])
    solid = block.difference(cut, engine="manifold")
    if roof == "pointed":
        # prism rising 15 mm from the 30 mm opening: every layer is carried
        # by the one below, so there is nothing to bridge
        apex = trimesh.creation.extrude_triangulation(
            vertices=[[-15, 0], [15, 0], [0, 15]], faces=[[0, 1, 2]], height=22
        )
        apex.apply_transform(trimesh.transformations.rotation_matrix(3.14159265 / 2, [1, 0, 0]))
        apex.apply_translation([0, 11, -34 / 2 + 14])
        solid = solid.difference(apex, engine="manifold")
    return grounded(solid)


def test_flat_roof_bridges_and_pointed_roof_does_not():
    flat = check_bridge(tunnel("flat"))
    pointed = check_bridge(tunnel("pointed"))
    # the tunnel is 30 mm wide, anchored both sides: reach is half the span
    assert 14.0 < flat.measured["max_reach_mm"] < 16.0
    assert flat.band == "fail"
    assert pointed.measured["max_reach_mm"] < 1.0
    assert pointed.band == "pass"
    assert pointed.index > flat.index


def test_solid_part_has_nothing_to_bridge():
    result = check_bridge(grounded(trimesh.creation.box(extents=[20, 20, 20])))
    assert result.measured["max_reach_mm"] == 0.0
    assert result.index == 1.0


def two_pegs(gap_mm: float):
    a = trimesh.creation.box(extents=[10, 10, 10])
    b = trimesh.creation.box(extents=[10, 10, 10])
    b.apply_translation([10 + gap_mm, 0, 0])
    return grounded(trimesh.util.concatenate([a, b]))


def test_clearance_separates_printable_from_fused():
    loose = check_clearance(two_pegs(0.5))
    tight = check_clearance(two_pegs(0.1))
    assert loose.band == "pass" and abs(loose.measured["min_gap_mm"] - 0.5) < 0.05
    assert tight.band == "fail"
    assert loose.index > tight.index


def test_clearance_fails_a_single_body():
    # a prompt asking for two free bodies is not satisfied by one fused solid
    result = check_clearance(grounded(trimesh.creation.box(extents=[20, 20, 20])))
    assert result.band == "fail"
    assert result.measured["body_count"] == 1


def test_criterion_checks_are_advisory_and_opt_in():
    mesh = grounded(trimesh.creation.box(extents=[20, 20, 20]))
    plain = score_mesh(mesh)
    tagged = score_mesh(mesh, criteria=["bridge_span", "fit_clearance"])
    assert [c.check for c in plain.checks] == ["min_wall", "overhang", "stability"]
    assert [c.check for c in tagged.checks][3:] == ["bridge_span", "fit_clearance"]
    # fit_clearance fails on this one-body part, yet must not move the headline
    assert any(c.band == "fail" and c.advisory for c in tagged.checks)
    assert tagged.printability == plain.printability


from cadclamp.engine.checks import (  # noqa: E402
    check_bed_interface,
    check_kinematic_sweep,
    check_living_hinge,
    check_load_orientation,
)


def tray(chamfer_mm: float):
    """160 x 120 x 12 open tray; optional 45-degree chamfer on the plate edges."""
    outer = trimesh.creation.box(extents=[160, 120, 12])
    inner = trimesh.creation.box(extents=[156, 116, 12])
    inner.apply_translation([0, 0, 2])
    body = outer.difference(inner, engine="manifold")
    if chamfer_mm:
        # cut the bottom outer edge back: a frustum-like wedge all round
        wedge = trimesh.creation.box(extents=[200, 200, chamfer_mm])
        wedge.apply_translation([0, 0, -6 + chamfer_mm / 2])
        keep = trimesh.creation.box(extents=[160 - 2 * chamfer_mm, 120 - 2 * chamfer_mm, chamfer_mm])
        keep.apply_translation([0, 0, -6 + chamfer_mm / 2])
        body = body.difference(wedge.difference(keep, engine="manifold"), engine="manifold")
    return grounded(body)


def test_bed_interface_wants_a_bottom_chamfer_on_large_parts():
    plain = check_bed_interface(tray(0.0))
    chamfered = check_bed_interface(tray(1.0))
    assert plain.band == "fail"
    assert chamfered.band == "pass" and chamfered.measured["bottom_edge_inset_mm"] > 0.4
    small = check_bed_interface(grounded(trimesh.creation.box(extents=[40, 40, 10])))
    assert small.band == "pass"  # nothing to design on a small footprint


def clip(standing: bool):
    profile = trimesh.creation.box(extents=[50, 10, 8])  # long axis X when flat
    if standing:
        profile.apply_transform(trimesh.transformations.rotation_matrix(3.14159265 / 2, [0, 1, 0]))
    return grounded(profile)


def test_load_orientation_rejects_a_standing_flexure():
    assert check_load_orientation(clip(False)).band == "pass"
    standing = check_load_orientation(clip(True))
    assert standing.band == "fail" and standing.index == 0.0


def bearing(ridge: float, clearance: float):
    """Hub with a 45-degree ridge inside a ring; ridge 0 = nothing holds it in."""
    import numpy as np

    def revolve(profile):
        closed = np.array(profile + [profile[0]], dtype=float)  # revolve wants a closed loop
        solid = trimesh.creation.revolve(closed, sections=96)
        solid.merge_vertices()
        assert solid.is_watertight, "fixture must be a valid solid, as the gate guarantees in production"
        return solid

    hub = revolve([[3, 0], [10, 0], [10, 3], [10 + ridge, 6], [10, 9], [10, 12], [3, 12]])
    c = clearance
    ring = revolve([[10 + c, 0], [18, 0], [18, 12], [10 + c, 12], [10 + c, 9], [10 + ridge + c, 6], [10 + c, 3]])
    return grounded(trimesh.util.concatenate([hub, ring]))


def test_kinematic_sweep_distinguishes_captive_free_and_fused():
    good = check_kinematic_sweep(bearing(ridge=3.0, clearance=0.5))
    loose = check_kinematic_sweep(bearing(ridge=0.0, clearance=0.5))
    fused = check_kinematic_sweep(bearing(ridge=3.0, clearance=-0.5))
    assert good.band == "pass" and good.measured["captive"] and good.measured["turns_freely"]
    assert loose.band == "warn" and not loose.measured["captive"]
    assert fused.band == "fail" and not fused.measured["turns_freely"]


def panels(web_mm: float):
    a = trimesh.creation.box(extents=[40, 30, 3]); a.apply_translation([-22, 0, 1.5])
    b = trimesh.creation.box(extents=[40, 30, 3]); b.apply_translation([22, 0, 1.5])
    web = trimesh.creation.box(extents=[4.2, 30, web_mm]); web.apply_translation([0, 0, web_mm / 2])
    return grounded(a.union(b, engine="manifold").union(web, engine="manifold"))


def test_living_hinge_band():
    assert check_living_hinge(panels(0.6)).band == "pass"
    assert check_living_hinge(panels(2.0)).band == "fail"  # too thick to flex
