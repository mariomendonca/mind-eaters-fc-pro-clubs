import asyncio
import json

from app import collector, queries
from app.collector import collect_once, run_forever
from app.config import Settings
from app.seasons import Snap, detect_periods
from app.store import save_bundle
from tests.factories import FakeEASource, make_bundle, match, t


# I-1: the collector loop survives any error, and health reports a dead collector
def test_run_forever_survives_errors(db_path, monkeypatch):
    calls = []

    def flaky(conn, source, now):
        calls.append(now)
        if len(calls) == 1:
            raise RuntimeError("database is locked")
        if len(calls) >= 3:
            raise asyncio.CancelledError
        return True

    monkeypatch.setattr(collector, "collect_once", flaky)
    try:
        asyncio.run(run_forever(Settings(db_path=db_path, collect_interval_s=0), source=None))
    except asyncio.CancelledError:
        pass
    assert len(calls) == 3


def test_health_fails_when_collector_task_died(db_path, conn):
    from fastapi.testclient import TestClient
    from app.main import create_app

    app = create_app(Settings(db_path=db_path, collector_enabled=False))
    with TestClient(app) as client:
        loop = asyncio.new_event_loop()
        dead = loop.create_future()
        dead.set_exception(RuntimeError("boom"))
        app.state.collector_task = dead
        r = client.get("/api/health")
        loop.close()
    assert r.status_code == 503 and r.json()["status"] == "collector stopped"


# I-2: a season reset closes the old season at the last snapshot before the reset
def test_season_reset_boundary_is_last_snapshot_before_reset():
    a, b = detect_periods([Snap(t(0), 50, 2, 4, 0), Snap(t(1), 60, 2, 4, 0), Snap(t(2), 1, 2, 0, 0)])
    assert a.ended_at == t(1) and b.started_at == t(1)
    assert a.campaigns[-1].ended_at == t(1) and b.campaigns[0].started_at == t(1)
    assert a.last_snap.season_games == 60


def test_first_match_of_new_season_counts_in_new_season(conn):
    save_bundle(conn, make_bundle(fetched_at=t(0), season=dict(make_bundle().season, gamesPlayed=60)))
    reset = dict(make_bundle().season, gamesPlayed=1, wins=1, ties=0, losses=0)
    first_of_new = match("151090313499999", t(0.5), "New Season FC", 2, 0)
    save_bundle(conn, make_bundle(fetched_at=t(1), season=reset, matches=[first_of_new], match_players=[], raw_matches=[]))
    new, old = queries.get_seasons(conn)["eaSeasons"]
    assert new["campaigns"][0]["wins"] == 1
    assert old["campaigns"][0]["wins"] + old["campaigns"][0]["draws"] + old["campaigns"][0]["losses"] == 3


# I-3: member stats history is kept
def test_member_snapshots_written_only_on_change(conn):
    save_bundle(conn, make_bundle(fetched_at=t(0)))
    save_bundle(conn, make_bundle(fetched_at=t(1)))
    changed = [dict(m) for m in make_bundle().members]
    changed[0]["goals"] += 1
    save_bundle(conn, make_bundle(fetched_at=t(2), members=changed))
    rows = conn.execute("select taken_at, data_json from member_snapshots where gamertag='netozeraaa' order by taken_at").fetchall()
    assert [r["taken_at"] for r in rows] == [t(0).isoformat(), t(2).isoformat()]
    assert json.loads(rows[-1]["data_json"])["goals"] == 118


# I-4: an empty answer from EA is a failure, not a success
def test_empty_bundle_counts_as_failure(conn):
    empty = make_bundle(season=None, overall=None, members=[], matches=[], match_players=[], raw_matches=[], details=None)
    assert collect_once(conn, FakeEASource([empty]), now=t(0)) is False
    row = conn.execute("select last_error, last_success_at from collector_status").fetchone()
    assert row["last_error"].startswith("EmptyResponse") and row["last_success_at"] is None


# I-5: matches are paginated without splitting a session
def test_list_matches_pagination_keeps_sessions_whole(conn):
    ms = [match(str(1000 + i), t(-i * 0.5), f"Opp {i}", 1, 0) for i in range(4)]       # one session, 4 games
    ms += [match(str(2000 + i), t(-48 - i * 0.5), f"Old {i}", 0, 1) for i in range(3)]  # older session
    save_bundle(conn, make_bundle(matches=ms, match_players=[], raw_matches=[]))
    page1 = queries.list_matches(conn, 2)
    assert [len(s["matches"]) for s in page1["sessions"]] == [4]
    assert page1["nextBefore"] == t(-1.5).isoformat()
    page2 = queries.list_matches(conn, 2, before=page1["nextBefore"])
    assert [len(s["matches"]) for s in page2["sessions"]] == [3]
    assert page2["nextBefore"] is None


def test_matches_route_accepts_before(conn, client):
    save_bundle(conn, make_bundle())
    body = client.get("/api/matches", params={"limit": 50, "before": t(0).isoformat()}).json()
    assert "nextBefore" in body and body["sessions"]


# M-1 (promoted): season/division come from the last snapshot that had a season row
def test_overview_falls_back_to_last_season_row(conn):
    save_bundle(conn, make_bundle(fetched_at=t(0)))
    save_bundle(conn, make_bundle(fetched_at=t(1), season=None))
    o = queries.get_overview(conn)
    assert o["season"]["points"] == 28 and o["club"]["division"] == 4
    assert o["updatedAt"] == t(1).isoformat()
