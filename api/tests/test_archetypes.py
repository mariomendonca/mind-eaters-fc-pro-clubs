from app import queries
from app.archetypes import archetype
from app.store import save_bundle
from tests.factories import PLAYER_IDS, make_bundle, match, mp, t


def raw(match_id, archetypes: dict):
    """EA raw match payload with each player's archetypeid (keyed by club, then player id)."""
    return {"matchId": match_id, "players": {
        "1232878": {str(PLAYER_IDS[tag]): {"playername": tag, "archetypeid": str(aid)} for tag, aid in archetypes.items()},
        "900": {"555": {"playername": "rival", "archetypeid": "11"}},
    }}


def seed(conn):
    matches = [match("1", t(1), "A", 2, 1), match("2", t(2), "B", 0, 1), match("3", t(3), "C", 1, 1)]
    players = [
        mp("1", t(1), "bielpontes04", 8.0, goals=2, motm=True), mp("1", t(1), "netozeraaa", 7.0, assists=1),
        mp("2", t(2), "bielpontes04", 6.0), mp("2", t(2), "netozeraaa", 7.0),
        mp("3", t(3), "bielpontes04", 7.0, goals=1),
    ]
    raws = [raw("1", {"bielpontes04": 3, "netozeraaa": 8}), raw("2", {"bielpontes04": 3, "netozeraaa": 8}),
            raw("3", {"bielpontes04": 12})]
    save_bundle(conn, make_bundle(matches=matches, match_players=players, raw_matches=raws))


def test_archetype_names():
    assert archetype("12") == {"id": 12, "name": "Finisher"}
    assert archetype(30) == {"id": 30, "name": "Goalkeeper"}
    assert archetype(99) == {"id": 99, "name": "Archetype #99"}
    assert archetype(None) is None


def test_player_archetype_history_and_splits(conn):
    seed(conn)
    data = queries.get_player(conn, "bielpontes04")
    assert data["player"]["archetype"] == {"id": 12, "name": "Finisher"}  # most recent match
    assert [h["archetype"]["name"] for h in data["history"]] == ["Progressor", "Progressor", "Finisher"]
    prog, fin = data["archetypes"]
    assert prog["name"] == "Progressor" and (prog["games"], prog["wins"], prog["losses"], prog["goals"], prog["motm"]) == (2, 1, 1, 2, 1)
    assert prog["avgRating"] == 7.0
    assert fin["name"] == "Finisher" and (fin["games"], fin["draws"], fin["goals"]) == (1, 1, 1)


def test_players_list_and_match_carry_archetype(conn):
    seed(conn)
    by_tag = {p["gamertag"]: p for p in queries.list_players(conn)}
    assert by_tag["netozeraaa"]["archetype"]["name"] == "Maestro"
    assert by_tag["CUFIS"]["archetype"] is None  # no saved matches
    players = {p["gamertag"]: p for p in queries.get_match(conn, "1")["players"]}
    assert players["bielpontes04"]["archetype"]["name"] == "Progressor"


def test_team_record_by_archetype_counts_each_match_once(conn):
    seed(conn)
    out = {a["name"]: a for a in queries.get_archetypes(conn)["archetypes"]}
    assert set(out) == {"Progressor", "Maestro", "Finisher"}  # opponents' archetypes are ignored
    p = out["Progressor"]
    assert (p["games"], p["wins"], p["losses"], p["winRate"], p["playerGames"], p["goals"]) == (2, 1, 1, 50, 2, 2)
    assert out["Maestro"]["assists"] == 1


def test_players_within_each_archetype(conn):
    seed(conn)
    data = queries.get_archetypes(conn)
    prog = next(a for a in data["archetypes"] if a["name"] == "Progressor")
    (path,) = prog["players"]
    assert path["displayName"] == "Path"
    assert (path["games"], path["wins"], path["losses"], path["goals"], path["motm"], path["avgRating"]) == (2, 1, 1, 2, 1, 7.0)
    assert path["lastPlayed"] == t(2).isoformat()
    assert "Magician" in data["unused"] and "Progressor" not in data["unused"]
    assert data["unused"].count("Goalkeeper") == 1


def test_missing_raw_payload_means_no_archetype(conn):
    save_bundle(conn, make_bundle(matches=[match("1", t(1), "A", 1, 0)], match_players=[mp("1", t(1), "CUFIS", 7.0)], raw_matches=[]))
    assert queries.get_player(conn, "CUFIS")["history"][0]["archetype"] is None
    assert queries.get_archetypes(conn)["archetypes"] == []


def test_endpoint(client):
    assert client.get("/api/archetypes").json()["archetypes"] == []
