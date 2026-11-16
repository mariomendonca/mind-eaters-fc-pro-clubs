from app import queries
from app.store import save_bundle
from tests.factories import make_bundle, match, t


def bundle(matches):
    return make_bundle(matches=matches, match_players=[], raw_matches=[{"matchId": str(m["matchId"])} for m in matches])


def opp(m, opponent_id, crest="https://example.test/c.png"):
    return dict(m, opponentId=opponent_id, opponentCrestUrl=crest)


def test_empty(conn):
    assert queries.list_opponents(conn) == []


def test_head_to_head_record_per_club(conn):
    save_bundle(conn, bundle([
        opp(match("1", t(0), "Old Name FC", 2, 1), 10),
        opp(match("2", t(2), "Tropa", 1, 1), 20),
        opp(match("3", t(3), "New Name FC", 0, 3), 10, crest="https://example.test/new.png"),
        opp(match("4", t(4), "Lone FC", 4, 0), 30),
    ]))
    out = queries.list_opponents(conn)
    assert [o["opponentId"] for o in out] == [10, 30, 20]  # most played first, then most recent
    club = out[0]
    assert club["name"] == "New Name FC" and club["crestUrl"] == "https://example.test/new.png"  # latest wins
    assert (club["games"], club["wins"], club["draws"], club["losses"]) == (2, 1, 0, 1)
    assert (club["goals"], club["goalsAgainst"]) == (2, 4)
    assert club["lastPlayed"] == t(3).isoformat()
    assert [m["matchId"] for m in club["matches"]] == ["3", "1"]


def test_endpoint(client):
    r = client.get("/api/opponents")
    assert r.status_code == 200 and r.json() == []
