from datetime import datetime, timezone

from app import queries
from app.store import save_bundle
from tests.factories import SP, make_bundle, match


def at(hour, minute=0, day=30):
    return datetime(2026, 10, day, hour, minute, tzinfo=SP)


def bundle(matches):
    return make_bundle(matches=matches, match_players=[], raw_matches=[{"matchId": str(m["matchId"])} for m in matches])


def by_slot(data):
    return {s["slot"]: s for s in data["slots"]}


def test_empty_db_returns_three_empty_slots(conn):
    data = queries.get_time_of_day(conn)
    assert [s["slot"] for s in data["slots"]] == ["morning", "afternoon", "night"]
    assert all(s["games"] == 0 and s["winRate"] == 0 for s in data["slots"])


def test_groups_results_by_local_hour(conn):
    save_bundle(conn, bundle([
        match("1", at(6), "A", 2, 0),        # morning starts at 06:00
        match("2", at(11, 59), "B", 0, 1),   # still morning
        match("3", at(12), "C", 1, 1),       # afternoon starts at 12:00
        match("4", at(17, 59), "D", 3, 1),
        match("5", at(18), "E", 3, 0),       # night starts at 18:00
        match("6", at(2, day=31), "F", 0, 4),  # after midnight is still night
        match("7", at(5, 59, day=31), "G", 2, 1),
    ]))
    s = by_slot(queries.get_time_of_day(conn))
    assert (s["morning"]["wins"], s["morning"]["draws"], s["morning"]["losses"]) == (1, 0, 1)
    assert (s["afternoon"]["wins"], s["afternoon"]["draws"], s["afternoon"]["losses"]) == (1, 1, 0)
    assert (s["night"]["wins"], s["night"]["draws"], s["night"]["losses"]) == (2, 0, 1)
    assert s["night"]["games"] == 3 and s["night"]["winRate"] == 67
    assert s["morning"]["winRate"] == 50


def test_uses_club_timezone_not_utc(conn):
    # 22:00 UTC is 19:00 in São Paulo → night, not "afternoon" or next-day morning
    save_bundle(conn, bundle([match("1", datetime(2026, 10, 30, 22, 0, tzinfo=timezone.utc), "A", 1, 0)]))
    assert by_slot(queries.get_time_of_day(conn))["night"]["wins"] == 1


def test_endpoint(client):
    r = client.get("/api/time-of-day")
    assert r.status_code == 200 and len(r.json()["slots"]) == 3
