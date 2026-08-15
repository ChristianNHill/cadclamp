import pytest

from cadclamp.engine.composite import two_tier_index, weighted_geometric_mean
from cadclamp.engine.score import score_mesh


def test_two_tier_index_shape():
    assert two_tier_index(0.2, 0.45, 0.8) < 0.05
    assert two_tier_index(1.5, 0.45, 0.8) > 0.95
    mid = two_tier_index(0.625, 0.45, 0.8)
    assert 0.4 < mid < 0.6
    with pytest.raises(ValueError):
        two_tier_index(1.0, 0.8, 0.8)


def test_geometric_mean_tanks_on_one_bad_index():
    good = weighted_geometric_mean({"a": 0.9, "b": 0.9, "c": 0.9})
    bad = weighted_geometric_mean({"a": 0.9, "b": 0.9, "c": 0.01})
    assert good > 0.85
    assert bad < 0.35


def test_good_cube_scores_high(good_cube):
    card = score_mesh(good_cube, part="cube")
    assert not card.gated_out
    assert card.printability > 0.8
    assert len(card.checks) == 3


def test_soup_gated_out(open_soup):
    card = score_mesh(open_soup, part="soup")
    assert card.gated_out
    assert card.failure_code == "not_watertight"
    assert card.printability == 0.0
    assert card.checks == []


def test_report_card_serializes(good_cube):
    card = score_mesh(good_cube)
    payload = card.to_json()
    assert "printability" in payload
    assert "min_wall" in payload
