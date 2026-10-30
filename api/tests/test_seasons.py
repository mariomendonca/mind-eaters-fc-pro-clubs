from app.seasons import Snap, detect_periods
from tests.factories import t


def test_single_snapshot_is_partial_in_progress():
    [s] = detect_periods([Snap(t(0), 38, 4, 2, 0)])
    assert s.partial and s.promotions_before_tracking == 2
    assert s.ended_at is None and s.started_at == t(0)
    assert [(c.division, c.outcome, c.partial) for c in s.campaigns] == [(4, "in_progress", True)]


def test_promotion_starts_new_campaign():
    [s] = detect_periods([Snap(t(0), 38, 4, 2, 0), Snap(t(1), 45, 4, 2, 0), Snap(t(2), 48, 3, 3, 0)])
    assert [(c.division, c.outcome) for c in s.campaigns] == [(4, "promoted"), (3, "in_progress")]
    assert s.campaigns[0].ended_at == t(2) and s.campaigns[1].started_at == t(2)
    assert s.campaigns[1].partial is False and s.campaigns[1].ended_at is None


def test_relegation():
    [s] = detect_periods([Snap(t(0), 10, 3, 0, 0), Snap(t(1), 20, 4, 0, 1)])
    assert s.campaigns[0].outcome == "relegated"


def test_games_drop_starts_new_season():
    a, b = detect_periods([Snap(t(0), 60, 2, 4, 0), Snap(t(5), 2, 2, 0, 0)])
    assert a.ended_at == t(0) and a.campaigns[-1].outcome == "stayed" and a.campaigns[-1].ended_at == t(0)
    assert b.partial is False and b.promotions_before_tracking == 0 and b.started_at == t(0)
    assert [(c.division, c.outcome, c.partial) for c in b.campaigns] == [(2, "in_progress", False)]
    assert a.last_snap.season_games == 60 and b.last_snap.season_games == 2


def test_new_season_with_different_division():
    a, b = detect_periods([Snap(t(0), 60, 2, 4, 0), Snap(t(5), 1, 3, 0, 0)])
    assert a.campaigns[-1].outcome == "stayed"
    assert b.campaigns[0].division == 3


def test_unsorted_input_is_sorted():
    [s] = detect_periods([Snap(t(2), 48, 3, 3, 0), Snap(t(0), 38, 4, 2, 0)])
    assert [c.division for c in s.campaigns] == [4, 3]


def test_empty_input():
    assert detect_periods([]) == []
