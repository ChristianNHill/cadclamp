from __future__ import annotations

import numpy as np
import pytest
import trimesh


def _grounded(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    mesh.apply_translation([0, 0, -mesh.bounds[0][2]])
    return mesh


@pytest.fixture
def good_cube() -> trimesh.Trimesh:
    """20 mm cube on the plate: thick, no overhangs, stable."""
    return _grounded(trimesh.creation.box(extents=[20, 20, 20]))


@pytest.fixture
def thin_wall_box() -> trimesh.Trimesh:
    """Open-top box with 0.4 mm walls — below one FDM perimeter pair."""
    outer = trimesh.creation.box(extents=[30, 30, 15])
    inner = trimesh.creation.box(extents=[29.2, 29.2, 15])
    inner.apply_translation([0, 0, 3.0])  # 3 mm floor, 0.4 mm side walls
    box = outer.difference(inner, engine="manifold")
    return _grounded(box)


@pytest.fixture
def mushroom() -> trimesh.Trimesh:
    """Wide disc on a narrow pillar: large horizontal underside far off the plate."""
    pillar = trimesh.creation.cylinder(radius=5, height=20, sections=64)
    pillar.apply_translation([0, 0, 10])
    cap = trimesh.creation.cylinder(radius=15, height=3, sections=64)
    cap.apply_translation([0, 0, 21.5])
    return _grounded(pillar.union(cap, engine="manifold"))


@pytest.fixture
def tall_pin() -> trimesh.Trimesh:
    """2 mm diameter, 60 mm tall pin: tips over on the plate."""
    pin = trimesh.creation.cylinder(radius=1.0, height=60, sections=48)
    pin.apply_translation([0, 0, 30])
    return _grounded(pin)


@pytest.fixture
def open_soup() -> trimesh.Trimesh:
    """Cube with two faces deleted: not watertight."""
    cube = trimesh.creation.box(extents=[10, 10, 10])
    return trimesh.Trimesh(vertices=cube.vertices, faces=cube.faces[:-2], process=False)
