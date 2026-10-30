from app import queries
from app.store import save_bundle
from tests.factories import MATCH_ID, make_bundle, match, mp, t


def test_overview_none_when_empty(conn):
    assert queries.get_overview(conn) is None


def test_overview_shape(conn):
    save_bundle(conn, make_bundle())
    o = queries.get_overview(conn)
    assert o["club"] == {"clubId": 1232878, "name": "Mind Eaters FC", "crestUrl": "https://example.test/crest.png",
                         "stadium": "Estádio de ní", "division": 4, "bestDivision": 2, "promotions": 6,
                         "relegations": 0, "skillRating": 1782}
    assert o["season"] == {"gamesPlayed": 38, "wins": 19, "ties": 7, "losses": 12, "points": 28,
                           "goals": 120, "goalsAgainst": 108}
    assert o["allTime"]["gamesPlayed"] == 123 and o["allTime"]["unbeatenStreak"] == 2
    first = o["recentMatches"][0]
    assert first["matchId"] == MATCH_ID and first["opponentName"] == "Tamandua Xereka"
    assert first["motm"] == {"gamertag": "bielpontes04", "displayName": "Path"}
    assert first["best"] == {"gamertag": "netozeraaa", "displayName": "Reginaldo", "rating": 10.0}
    assert o["leaders"]["goals"] == {"gamertag": "netozeraaa", "displayName": "Reginaldo", "value": 117}
    assert o["leaders"]["rating"]["value"] == 8.2
    assert o["mvpCounts"][0] == {"gamertag": "bielpontes04", "displayName": "Path", "count": 2}
    assert [p["gamertag"] for p in o["players"]][:2] == ["netozeraaa", "Baby2KK"]
    assert o["updatedAt"] == t(0).isoformat()


def test_overview_without_club_info_uses_season_row(conn):
    save_bundle(conn, make_bundle(details=None))
    club = queries.get_overview(conn)["club"]
    assert club["name"] == "Mind Eaters FC" and club["stadium"] == ""


def test_match_without_motm(conn):
    save_bundle(conn, make_bundle())
    mt = queries.get_match(conn, "151090313490050")["match"]
    assert mt["motm"] is None and mt["best"]["displayName"] == "Path"


def test_display_name_falls_back_to_gamertag(conn):
    b = make_bundle()
    b.match_players.append(mp(MATCH_ID, t(-14), "ghost99", 6.0))
    save_bundle(conn, b)
    names = [p["displayName"] for p in queries.get_match(conn, MATCH_ID)["players"]]
    assert "ghost99" in names


def test_match_players_sorted_by_rating(conn):
    save_bundle(conn, make_bundle())
    players = queries.get_match(conn, MATCH_ID)["players"]
    assert [p["rating"] for p in players] == sorted([p["rating"] for p in players], reverse=True)
    assert players[1]["manOfTheMatch"] is True and players[1]["secondsPlayed"] == 5400


def test_get_match_unknown(conn):
    assert queries.get_match(conn, "1") is None


def test_player_history_oldest_first(conn):
    save_bundle(conn, make_bundle())
    p = queries.get_player(conn, "bielpontes04")
    assert p["player"]["displayName"] == "Path" and p["player"]["passSuccessRate"] == 83
    assert [h["matchId"] for h in p["history"]] == ["151090313490050", "151090313490100", MATCH_ID]
    assert p["tracked"] == {"games": 3, "goals": 4, "assists": 5, "motm": 2, "avgRating": 9.2}


def test_get_player_unknown_returns_none(conn):
    save_bundle(conn, make_bundle())
    assert queries.get_player(conn, "nope") is None


def test_list_matches_sessions(conn):
    save_bundle(conn, make_bundle())
    [s] = queries.list_matches(conn, 50)["sessions"]
    assert (s["wins"], s["draws"], s["losses"]) == (1, 1, 1)
    assert s["matches"][0]["matchId"] == MATCH_ID


def test_list_matches_limit(conn):
    save_bundle(conn, make_bundle())
    # limit 2, but all 3 fixture matches are one session, so the page keeps it whole
    page = queries.list_matches(conn, 2)
    assert sum(len(s["matches"]) for s in page["sessions"]) == 3 and page["nextBefore"] is None


def test_seasons_partial_first(conn):
    save_bundle(conn, make_bundle())
    [s] = queries.get_seasons(conn)["eaSeasons"]
    assert s["partial"] and s["promotionsBeforeTracking"] == 2 and s["endedAt"] is None
    assert s["totals"] == {"gamesPlayed": 38, "wins": 19, "ties": 7, "losses": 12, "points": 28,
                           "goals": 120, "goalsAgainst": 108, "promotions": 2, "relegations": 0}
    [c] = s["campaigns"]
    assert c["outcome"] == "in_progress" and c["partial"] and c["division"] == 4
    assert (c["wins"], c["draws"], c["losses"], c["goals"], c["goalsAgainst"]) == (1, 1, 1, 11, 9)
    assert c["topScorer"] == {"gamertag": "Baby2KK", "displayName": "C. Carvalho", "value": 5}
    assert c["topMvp"] == {"gamertag": "bielpontes04", "displayName": "Path", "value": 2}


def test_seasons_campaign_split_by_time(conn):
    save_bundle(conn, make_bundle())
    promoted_season = dict(make_bundle().season, currentDivision=3, promotions=3, gamesPlayed=40)
    later = match("151090313499999", t(2), "Later FC", 1, 0)
    save_bundle(conn, make_bundle(fetched_at=t(1), season=promoted_season, matches=[later], match_players=[], raw_matches=[]))
    [s] = queries.get_seasons(conn)["eaSeasons"]
    newest, oldest = s["campaigns"]
    assert (newest["division"], newest["outcome"], newest["wins"]) == (3, "in_progress", 1)
    assert (oldest["division"], oldest["outcome"], oldest["wins"] + oldest["draws"] + oldest["losses"]) == (4, "promoted", 3)
    assert newest["topScorer"] is None


def test_seasons_empty(conn):
    assert queries.get_seasons(conn) == {"eaSeasons": []}


def test_status_empty(conn):
    assert queries.get_status(conn) == {"lastAttemptAt": None, "lastSuccessAt": None, "lastError": None}
