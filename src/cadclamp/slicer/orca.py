"""Slice parts with OrcaSlicer on current popular printers (advisory check).

OrcaSlicer is AGPL, so it is only ever run as a subprocess. Each machine is
the newest mainstream 0.4 mm machine of a big brand, with that vendor's own
standard 0.20 mm process and default PLA, flattened from Orca's inheriting
system profiles so the command line gets complete settings. Parts are sliced
in the orientation they were modelled in (+Z up, no auto-orient) with
supports enabled using the vendor's own support settings (type, threshold
angle, bridge and build-plate-only rules); support is measured from the G-code, so
"prints without support" is checked by a real slicer rather than inferred.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
from functools import lru_cache
from pathlib import Path

ORCA = os.environ.get("CADCLAMP_ORCA", "/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer")
PROFILES = Path(os.environ.get("CADCLAMP_ORCA_PROFILES", "/Applications/OrcaSlicer.app/Contents/Resources/profiles"))

# key: (vendor folder, machine preset, process preset). Filament is the
# machine's own default_filament_profile.
MACHINES = {
    "bambu-p2s": ("BBL", "Bambu Lab P2S 0.4 nozzle", "0.20mm Standard @BBL P2S"),
    "prusa-core-one": ("Prusa", "Prusa CORE One 0.4 nozzle", "0.20mm SPEED @CORE One 0.4"),
    "creality-k2-plus": ("Creality", "Creality K2 Plus 0.4 nozzle", "0.20mm Standard @Creality K2 Plus 0.4 nozzle"),
    "elegoo-cc2": ("Elegoo", "Elegoo Centauri Carbon 2 0.4 nozzle", "0.20mm Standard @Elegoo CC2 0.4 nozzle"),
    "anycubic-kobra-s1": ("Anycubic", "Anycubic Kobra S1 0.4 nozzle", "0.20mm Standard @Anycubic Kobra S1 0.4 nozzle"),
}


@lru_cache(maxsize=None)
def _index(vendor: str) -> dict[str, Path]:
    """Preset name -> file, for a vendor plus Orca's shared filament library."""
    out: dict[str, Path] = {}
    for root in (PROFILES / "OrcaFilamentLibrary", PROFILES / vendor):
        for path in root.rglob("*.json"):
            try:
                name = json.loads(path.read_text()).get("name")
            except (ValueError, UnicodeDecodeError):
                continue
            if name:
                out[name] = path  # vendor presets override the library
    return out


def resolve(vendor: str, name: str) -> dict:
    """Merge a preset with every preset it inherits from (child wins)."""
    chain = []
    while name:
        data = json.loads(_index(vendor)[name].read_text())
        chain.append(data)
        name = data.get("inherits")
    merged: dict = {}
    for data in reversed(chain):
        merged.update(data)
    merged.pop("inherits", None)
    merged["from"] = "system"  # CLI matches compatibility on system preset names
    return merged


def _write_settings(machine: str, workdir: Path, support: bool) -> tuple[Path, Path, Path]:
    vendor, machine_name, process_name = MACHINES[machine]
    printer = resolve(vendor, machine_name)
    process = resolve(vendor, process_name)
    filament_name = printer["default_filament_profile"]
    if isinstance(filament_name, list):
        filament_name = filament_name[0]
    filament = resolve(vendor, filament_name)
    # the CLI checks process/filament compatibility by printer preset name.
    # Support style, threshold angle, bridge and build-plate-only settings stay
    # the vendor's own (tree on Bambu/Elegoo/Anycubic): only "on" is ours.
    process.update({
        "enable_support": "1" if support else "0",
        "compatible_printers": [machine_name],
        "compatible_printers_condition": "",
    })
    filament["compatible_printers"] = [machine_name]
    filament["compatible_printers_condition"] = ""
    paths = []
    for kind, data in (("machine", printer), ("process", process), ("filament", filament)):
        path = workdir / f"{kind}.json"
        path.write_text(json.dumps(data))
        paths.append(path)
    return tuple(paths)


def support_settings(machine: str) -> dict:
    """The vendor support settings a slice runs with, for the report."""
    vendor, _, process_name = MACHINES[machine]
    process = resolve(vendor, process_name)
    keys = ("support_type", "support_threshold_angle", "bridge_no_support", "support_on_build_plate_only")
    return {k: process.get(k) for k in keys}


_TYPE = re.compile(r"^;\s*(?:TYPE|FEATURE):\s*(.+)$")


def extrusion_by_feature(gcode: str) -> dict[str, float]:
    """Filament length (mm) extruded per feature type, M82 or M83."""
    per: dict[str, float] = {}
    feature, relative, last_e = "unknown", False, 0.0
    retracted = 0.0  # filament pulled back; pushing it back is not extrusion
    for line in gcode.splitlines():
        if line.startswith(";"):
            match = _TYPE.match(line)
            if match:
                feature = match.group(1).strip()
            continue
        head = line.split(";", 1)[0].strip()
        if not head:
            continue
        if head.startswith("M83"):
            relative = True
        elif head.startswith("M82"):
            relative = False
        elif head.startswith("G92"):
            e = re.search(r"\bE(-?[\d.]+)", head)
            if e:
                last_e = float(e.group(1))
        elif head.startswith(("G1", "G0", "G2", "G3")):
            e = re.search(r"\bE(-?[\d.]+)", head)
            if e:
                value = float(e.group(1))
                delta = value if relative else value - last_e
                if not relative:
                    last_e = value
                if delta < 0:
                    retracted -= delta
                elif delta > 0:
                    restore = min(delta, retracted)
                    retracted -= restore
                    if delta > restore:
                        per[feature] = per.get(feature, 0.0) + delta - restore
    return per


def slice_part(stl: str | Path, machine: str, *, support: bool = True, timeout_s: int = 300) -> dict:
    """Slice one STL on one machine. Returns what the slicer reported."""
    stl = Path(stl).resolve()  # Orca runs from a temp dir
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        machine_json, process_json, filament_json = _write_settings(machine, workdir, support)
        out = workdir / "out"
        out.mkdir()
        cmd = [
            ORCA,
            "--load-settings", f"{machine_json};{process_json}",
            "--load-filaments", str(filament_json),
            "--orient", "0",
            "--arrange", "1",
            "--ensure-on-bed",
            "--slice", "0",
            "--outputdir", str(out),
            str(stl),
        ]
        start = time.monotonic()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, cwd=workdir)
        except subprocess.TimeoutExpired:
            return {"machine": machine, "sliced": False, "failure": "timeout", "seconds": timeout_s}
        seconds = time.monotonic() - start
        gcodes = sorted(out.rglob("*.gcode"))
        log = (proc.stdout + proc.stderr)[-3000:]
        if proc.returncode != 0 or not gcodes:
            return {"machine": machine, "sliced": False, "failure": f"exit {proc.returncode}", "log": log, "seconds": seconds}
        gcode = gcodes[0].read_text(errors="replace")
        # start-gcode purge lines ("Custom", untagged) and prime towers are
        # the printer's, not the part's
        per = {k: v for k, v in extrusion_by_feature(gcode).items()
               if k not in ("unknown", "Custom") and "tower" not in k.lower()}
        support_mm = sum(v for k, v in per.items() if "support" in k.lower())  # Support, Support interface, Support transition
        total_mm = sum(per.values())
        time_match = re.search(r"; model printing time:\s*([^;\n]+)", gcode) or re.search(
            r"; estimated printing time \(normal mode\)\s*=\s*(.+)", gcode)
        layers_match = re.search(r"; total layer number:\s*(\d+)", gcode)
        return {
            "machine": machine,
            "sliced": True,
            "support": support,
            "filament_mm": round(total_mm, 2),
            "support_mm": round(support_mm, 2),
            "support_fraction": round(support_mm / total_mm, 4) if total_mm else None,
            "features_mm": {k: round(v, 2) for k, v in per.items()},
            "print_time": time_match.group(1).strip() if time_match else None,
            "layers": int(layers_match.group(1)) if layers_match else None,
            "seconds": round(seconds, 1),
        }
