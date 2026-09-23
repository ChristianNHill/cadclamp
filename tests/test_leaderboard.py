"""The leaderboard rebuilds printability from saved report cards (--regrade);
it must reproduce the engine's composite, advisory checks excluded."""

import sys
from pathlib import Path

import trimesh

from cadclamp.engine.score import score_mesh

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import leaderboard  # noqa: E402


def test_regrade_matches_engine_composite_with_advisory_checks():
    # 160 mm plate with a sharp bottom edge: bed_interface fails, but it is
    # advisory, so the composite must not move
    plate = trimesh.creation.box(extents=[160, 120, 10])
    plate.apply_translation([0, 0, 5])
    card = score_mesh(plate, criteria=["bed_interface"])
    advisory = [c for c in card.checks if c.advisory]
    assert advisory and advisory[0].index < 0.5
    assert leaderboard.regrade({"report": card.to_dict()}) == card.printability
