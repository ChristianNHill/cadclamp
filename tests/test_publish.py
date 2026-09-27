"""The published leaderboard must have been produced by the current prompt
specs, engine, task and harness: changing any of them without re-grading
would publish numbers the code no longer produces."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

PUBLISHED = Path(__file__).parents[1] / "docs" / "leaderboard.json"


@pytest.mark.skipif(not PUBLISHED.exists(), reason="no published leaderboard yet")
def test_published_leaderboard_matches_current_versions():
    from publish_leaderboard import versions

    stamped = json.loads(PUBLISHED.read_text())["versions"]
    assert stamped == versions(), "docs/leaderboard.* is stale: regrade and run scripts/publish_leaderboard.py"
