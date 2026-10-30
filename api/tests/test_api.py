from fc_clubs_api import FC27HTTPError

from app.collector import collect_once
from tests.factories import MATCH_ID, FakeEASource, make_bundle, t


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_overview_503_when_empty(client):
    r = client.get("/api/overview")
    assert r.status_code == 503 and r.json()["detail"] == "no data yet"


def test_collect_then_overview(conn, client):
    assert collect_once(conn, FakeEASource([make_bundle()]), now=t(0)) is True
    assert client.get("/api/overview").json()["club"]["name"] == "Mind Eaters FC"


def test_collect_failure_keeps_data(conn, client):
    collect_once(conn, FakeEASource([make_bundle()]), now=t(0))
    assert collect_once(conn, FakeEASource([FC27HTTPError(403, "https://ea")]), now=t(1)) is False
    st = client.get("/api/status").json()
    assert st["lastError"].startswith("FC27HTTPError")
    assert st["lastSuccessAt"] == t(0).isoformat() and st["lastAttemptAt"] == t(1).isoformat()
    assert client.get("/api/overview").status_code == 200


def test_success_clears_error(conn):
    collect_once(conn, FakeEASource([RuntimeError("boom")]), now=t(0))
    collect_once(conn, FakeEASource([make_bundle()]), now=t(1))
    assert conn.execute("select last_error from collector_status").fetchone()[0] is None


def test_details_refetched_daily(conn):
    src = FakeEASource([make_bundle(), make_bundle(details=None), make_bundle()])
    collect_once(conn, src, now=t(0))
    collect_once(conn, src, now=t(1))
    collect_once(conn, src, now=t(25))
    assert src.calls == [True, False, True]


def test_unknown_match_404(client):
    assert client.get("/api/matches/1").status_code == 404


def test_unknown_player_404(client):
    assert client.get("/api/players/nobody").status_code == 404


def test_match_id_is_string(conn, client):
    collect_once(conn, FakeEASource([make_bundle()]), now=t(0))
    body = client.get(f"/api/matches/{MATCH_ID}").json()
    assert body["match"]["matchId"] == MATCH_ID
    first = client.get("/api/matches").json()["sessions"][0]["matches"][0]
    assert isinstance(first["matchId"], str)


def test_players_seasons_status_routes(conn, client):
    collect_once(conn, FakeEASource([make_bundle()]), now=t(0))
    assert client.get("/api/players").json()[0]["gamertag"] == "netozeraaa"
    assert client.get("/api/players/bielpontes04").json()["tracked"]["games"] == 3
    assert client.get("/api/seasons").json()["eaSeasons"][0]["partial"] is True
    assert client.get("/api/status").json()["lastError"] is None
