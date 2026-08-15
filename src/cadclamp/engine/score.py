from __future__ import annotations

from pathlib import Path
from typing import Any

import trimesh

from cadclamp.engine.checks import check_min_wall, check_overhang, check_stability
from cadclamp.engine.composite import weighted_geometric_mean
from cadclamp.engine.gates import load_mesh, run_gates
from cadclamp.engine.types import FAIL, ReportCard

ENGINE_VERSION = "0.1.0"

DEFAULT_PROCESS: dict[str, Any] = {
    "name": "fdm",
    "nozzle_mm": 0.4,
    "line_width_mm": 0.4,
    "layer_mm": 0.2,
    "material": "PLA",
}


def score_mesh(
    mesh: trimesh.Trimesh,
    part: str = "part",
    process: dict[str, Any] | None = None,
) -> ReportCard:
    process = {**DEFAULT_PROCESS, **(process or {})}
    card = ReportCard(part=part, engine_version=ENGINE_VERSION, process=process)

    card.gates = run_gates(mesh)
    failed = next((g for g in card.gates if g.status == FAIL), None)
    if failed is not None:
        card.failure_code = failed.code
        card.printability = 0.0
        return card

    card.checks = [
        check_min_wall(mesh, line_width_mm=process["line_width_mm"]),
        check_overhang(mesh, layer_mm=process["layer_mm"]),
        check_stability(mesh),
    ]
    card.printability = weighted_geometric_mean({c.check: c.index for c in card.checks})
    return card


def score_file(path: str | Path, process: dict[str, Any] | None = None) -> ReportCard:
    return score_mesh(load_mesh(path), part=Path(path).name, process=process)
