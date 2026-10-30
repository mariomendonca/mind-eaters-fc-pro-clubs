import json

from app.store import save_bundle
from tests.factories import MATCH_ID, make_bundle


def count(conn, table):
    return conn.execute(f"select count(*) from {table}").fetchone()[0]


def test_save_is_idempotent(conn):
    b = make_bundle()
    save_bundle(conn, b)
    save_bundle(conn, b)
    assert count(conn, "matches") == len(b.matches)
    assert count(conn, "match_players") == len(b.match_players)
    assert count(conn, "club_snapshots") == 2


def test_snapshot_columns(conn):
    save_bundle(conn, make_bundle())
    row = conn.execute("select season_games, division, season_promotions, season_relegations from club_snapshots").fetchone()
    assert tuple(row) == (38, 4, 2, 0)


def test_departed_member_kept(conn):
    save_bundle(conn, make_bundle())
    save_bundle(conn, make_bundle(members=[m for m in make_bundle().members if m["name"] != "bielpontes04"]))
    assert conn.execute("select 1 from members where gamertag='bielpontes04'").fetchone()


def test_match_row_and_raw_json(conn):
    save_bundle(conn, make_bundle())
    row = conn.execute("select * from matches where match_id=?", (MATCH_ID,)).fetchone()
    assert row["opponent_name"] == "Tamandua Xereka" and row["goals"] == 6 and row["result"] == "win"
    assert row["timestamp"] == "2026-10-29T22:00:00-03:00"
    assert json.loads(row["raw_json"])["matchId"] == MATCH_ID


def test_motm_stored(conn):
    save_bundle(conn, make_bundle())
    row = conn.execute("select gamertag from match_players where match_id=? and motm=1", (MATCH_ID,)).fetchone()
    assert row["gamertag"] == "bielpontes04"


def test_no_snapshot_without_club_data(conn):
    save_bundle(conn, make_bundle(season=None, overall=None))
    assert count(conn, "club_snapshots") == 0


def test_details_saved_only_when_present(conn):
    save_bundle(conn, make_bundle(details=None))
    assert count(conn, "club_info") == 0
    save_bundle(conn, make_bundle())
    assert json.loads(conn.execute("select data_json from club_info").fetchone()[0])["stadium"] == "Estádio de ní"
