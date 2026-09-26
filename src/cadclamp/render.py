"""Four-view renders of a part, for image feedback and contact sheets.

OpenSCAD renders `import()` of the STL (subprocess only: OpenSCAD is GPL).
Views: isometric, front (-Y), right (+X), top; the three orthographic ones
use orthographic projection. The sheet is labelled with the overall size in
mm, as a CAD viewer shows it - geometry only, no score or pass/fail.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import trimesh
from PIL import Image, ImageDraw, ImageFont

OPENSCAD = os.environ.get("CADCLAMP_OPENSCAD", "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD")
VIEWS = (  # label, rotation (rx, ry, rz), projection
    ("isometric", (55, 0, 25), "perspective"),
    ("front", (90, 0, 0), "ortho"),
    ("right", (90, 0, 90), "ortho"),
    ("top", (0, 0, 0), "ortho"),
)
CELL = 480


def _font(size: int):
    for name in ("/System/Library/Fonts/SFNSMono.ttf", "/System/Library/Fonts/Menlo.ttc"):
        if os.path.exists(name):
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def four_views(stl: str | Path, out: str | Path) -> Path:
    stl, out = Path(stl).resolve(), Path(out)
    ext = trimesh.load(str(stl), force="mesh").extents
    sheet = Image.new("RGB", (2 * CELL, 2 * CELL + 44), "white")
    draw = ImageDraw.Draw(sheet)
    with tempfile.TemporaryDirectory() as tmp:
        scad = Path(tmp) / "r.scad"
        scad.write_text(f'import("{stl}");\n')
        for i, (label, (rx, ry, rz), projection) in enumerate(VIEWS):
            png = Path(tmp) / f"{label}.png"
            subprocess.run(
                [OPENSCAD, "-o", str(png), f"--imgsize={CELL},{CELL}", "--autocenter", "--viewall",
                 f"--camera=0,0,0,{rx},{ry},{rz},0", f"--projection={projection}",
                 "--colorscheme=Tomorrow", str(scad)],
                capture_output=True, timeout=120,
            )
            x, y = (i % 2) * CELL, 44 + (i // 2) * CELL
            if png.exists():
                sheet.paste(Image.open(png).convert("RGB"), (x, y))
            draw.text((x + 10, y + 8), label, fill="black", font=_font(20))
    draw.text((12, 10), f"overall size  X {ext[0]:.1f} x Y {ext[1]:.1f} x Z {ext[2]:.1f} mm   (+Z up)",
              fill="black", font=_font(20))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out
