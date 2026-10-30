"""Persist a Bundle. Safe to call repeatedly with overlapping data."""
import json
import sqlite3
from datetime import datetime

from app.ea import Bundle


def _iso(value) -> str:
    return value.isoformat() if isinstance(value, datetime) else str(value)


def _dumps(value) -> str:
    return json.dumps(value, default=_iso, ensure_ascii=False)


def save_bundle(conn: sqlite3.Connection, bundle: Bundle) -> None:
    now = _iso(bundle.fetched_at)
    raw_by_id = {str(r.get("matchId")): r for r in bundle.raw_matches if isinstance(r, dict)}
    with conn:
        for m in bundle.matches:
            mid = str(m["matchId"])
            conn.execute(
                """INSERT OR IGNORE INTO matches
                   (match_id, timestamp, match_type, opponent_id, opponent_name, opponent_crest_url,
                    goals, goals_against, result, dnf, raw_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (mid, _iso(m["timestamp"]), m.get("matchType", "leagueMatch"), m.get("opponentId"),
                 m.get("opponentName"), m.get("opponentCrestUrl"), m.get("goals"), m.get("goalsAgainst"),
                 m.get("result"), int(bool(m.get("dnf"))),
                 _dumps(raw_by_id[mid]) if mid in raw_by_id else None),
            )

        known = {r[0] for r in conn.execute("SELECT match_id FROM matches")}
        for p in bundle.match_players:
            mid = str(p["matchId"])
            if mid not in known:
                continue
            conn.execute(
                """INSERT OR REPLACE INTO match_players
                   (match_id, player_id, gamertag, position, rating, goals, assists, shots, passes_made,
                    pass_attempts, tackles_made, tackle_attempts, saves, clean_sheet, motm, red_cards,
                    seconds_played)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (mid, p["playerId"], p["name"], p.get("position"), p.get("rating"), p.get("goals"),
                 p.get("assists"), p.get("shots"), p.get("passesMade"), p.get("passAttempts"),
                 p.get("tacklesMade"), p.get("tackleAttempts"), p.get("saves"), p.get("cleanSheet"),
                 int(bool(p.get("manOfTheMatch"))), p.get("redCards"), p.get("secondsPlayed")),
            )

        if bundle.season or bundle.overall:
            s = bundle.season or {}
            conn.execute(
                """INSERT INTO club_snapshots
                   (taken_at, season_json, overall_json, season_games, division, season_promotions,
                    season_relegations) VALUES (?,?,?,?,?,?,?)""",
                (now, _dumps(bundle.season) if bundle.season else None,
                 _dumps(bundle.overall) if bundle.overall else None,
                 s.get("gamesPlayed"), s.get("currentDivision"), s.get("promotions"), s.get("relegations")),
            )

        for mem in bundle.members:
            conn.execute(
                "INSERT OR REPLACE INTO members (gamertag, data_json, updated_at) VALUES (?,?,?)",
                (mem["name"], _dumps(mem), now),
            )

        if bundle.details:
            conn.execute(
                "INSERT OR REPLACE INTO club_info (id, data_json, updated_at) VALUES (1,?,?)",
                (_dumps(bundle.details), now),
            )
