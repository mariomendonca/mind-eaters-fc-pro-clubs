from app.sessions import group_sessions
from tests.factories import t


def m(mid, when, result="win"):
    return {"matchId": mid, "timestamp": when.isoformat(), "result": result}


def test_sessions_split_on_gap():
    s = group_sessions([m("1", t(0)), m("2", t(0.5)), m("3", t(5))])
    assert [[x["matchId"] for x in g["matches"]] for g in s] == [["3"], ["2", "1"]]
    assert s[1]["start"] == t(0).isoformat()


def test_session_counts():
    [g] = group_sessions([m("1", t(0)), m("2", t(0.3), "loss"), m("3", t(0.6))])
    assert (g["wins"], g["draws"], g["losses"]) == (2, 0, 1)


def test_exactly_two_hours_stays_together():
    assert len(group_sessions([m("1", t(0)), m("2", t(2))])) == 1


def test_empty():
    assert group_sessions([]) == []
