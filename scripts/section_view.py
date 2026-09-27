"""Cross-sections of a scored part next to its prompt's reference, for
reviewing spec flips: an outside render cannot show a missing cavity.

    CADCLAMP_OPENSCAD=... .venv/bin/python scripts/section_view.py t4-006 <sha1> [<sha1> ...]
        -> logs/sections/<prompt>__<sha1>.png (planes X=0 and Y=0, plus Z at mid height;
           blue = part, red dashed = reference outline)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402

from cadclamp.engine.gates import load_mesh  # noqa: E402
from cadclamp.mutants import render  # noqa: E402
from cadclamp.prompts import PROMPT_SETS, load_prompts  # noqa: E402

OUT = Path("logs/sections")
PLANES = {"Y=0 (XZ)": ([0, 1, 0], [0, 2]), "X=0 (YZ)": ([1, 0, 0], [1, 2]), "Z mid (XY)": ([0, 0, 1], [0, 1])}


def _polys(mesh, normal, origin, dims):
    sec = mesh.section(plane_origin=origin, plane_normal=normal)
    if sec is None:
        return []
    out = []
    for ent in sec.discrete:
        out.append(np.asarray(ent)[:, dims])
    return out


def _draw(ax, loops, fill: bool):
    if not loops:
        return
    verts, codes = [], []
    for loop in loops:
        verts.extend(loop.tolist())
        codes.extend([MplPath.MOVETO] + [MplPath.LINETO] * (len(loop) - 1))
    if fill:  # the part: solid blue (even-odd, so holes stay open)
        ax.add_patch(PathPatch(MplPath(verts, codes), facecolor="#6f9fe0", edgecolor="#1f4f9f", lw=0.6))
    else:  # the reference: red outline only
        ax.add_patch(PathPatch(MplPath(verts, codes), facecolor="none", edgecolor="#d62728", lw=1.3, ls="--"))


def view(prompt_id: str, sha: str, ref, out: Path) -> Path:
    mesh = load_mesh(Path("logs/meshes") / f"{sha}.stl")
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6))
    for ax, (label, (normal, dims)) in zip(axes, PLANES.items()):
        origin = [0, 0, (ref.bounds[0][2] + ref.bounds[1][2]) / 2] if normal[2] else [0, 0, 0]
        _draw(ax, _polys(mesh, normal, origin, dims), fill=True)
        _draw(ax, _polys(ref, normal, origin, dims), fill=False)
        lo = np.minimum(ref.bounds[0], mesh.bounds[0])[dims] - 2
        hi = np.maximum(ref.bounds[1], mesh.bounds[1])[dims] + 2
        ax.set_xlim(lo[0], hi[0])
        ax.set_ylim(lo[1], hi[1])
        ax.set_aspect("equal")
        ax.set_title(label, fontsize=10)
        ax.grid(alpha=0.2)
    fig.suptitle(f"{prompt_id}  {sha[:10]}   blue = part, red dashed = reference outline", fontsize=11)
    fig.tight_layout()
    fig.savefig(out, dpi=90)
    plt.close(fig)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("shas", nargs="+")
    a = ap.parse_args(argv)
    ref_path = next(path.parent / "reference" / f"{a.prompt}.scad" for path in PROMPT_SETS.values()
                    if any(p.id == a.prompt for p in load_prompts(path).prompts))
    ref = render(ref_path.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for sha in a.shas:
        print(view(a.prompt, sha, ref, OUT / f"{a.prompt}__{sha}.png"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
