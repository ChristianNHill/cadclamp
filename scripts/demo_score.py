"""Generate the planted-violation demo parts and score them via the CLI path."""

from __future__ import annotations

import sys
from pathlib import Path

import trimesh

OUT = Path(__file__).resolve().parent.parent / "demo_parts"


def grounded(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    mesh.apply_translation([0, 0, -mesh.bounds[0][2]])
    return mesh


def build_parts() -> dict[str, trimesh.Trimesh]:
    good = grounded(trimesh.creation.box(extents=[20, 20, 20]))

    outer = trimesh.creation.box(extents=[30, 30, 15])
    inner = trimesh.creation.box(extents=[29.2, 29.2, 15])
    inner.apply_translation([0, 0, 3.0])
    thin = grounded(outer.difference(inner, engine="manifold"))

    pillar = trimesh.creation.cylinder(radius=5, height=20, sections=64)
    pillar.apply_translation([0, 0, 10])
    cap = trimesh.creation.cylinder(radius=15, height=3, sections=64)
    cap.apply_translation([0, 0, 21.5])
    mushroom = grounded(pillar.union(cap, engine="manifold"))

    pin = trimesh.creation.cylinder(radius=1.0, height=60, sections=48)
    pin.apply_translation([0, 0, 30])
    pin = grounded(pin)

    cube = trimesh.creation.box(extents=[10, 10, 10])
    soup = trimesh.Trimesh(vertices=cube.vertices, faces=cube.faces[:-2], process=False)

    return {
        "good_cube.stl": good,
        "thin_wall_box.stl": thin,
        "mushroom.stl": mushroom,
        "tall_pin.stl": pin,
        "open_soup.stl": soup,
    }


def main() -> int:
    OUT.mkdir(exist_ok=True)
    paths = []
    for name, mesh in build_parts().items():
        path = OUT / name
        mesh.export(path)
        paths.append(str(path))

    from cadclamp.cli import main as cli_main

    return cli_main(["score", *paths, "--json", str(OUT / "reports.json")])


if __name__ == "__main__":
    sys.exit(main())
