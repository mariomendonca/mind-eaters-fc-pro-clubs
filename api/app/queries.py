"""Read models: turn stored rows into the JSON shapes of the API contract."""
import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional

from app.seasons import Snap, detect_periods
from app.sessions import group_sessions

PLAYER_FIELDS = (
    "position", "overall", "gamesPlayed", "winRate", "goals", "assists", "averageRating",
    "manOfTheMatch", "shotSuccessRate", "passesMade", "passSuccessRate", "tacklesMade",
    "tackleSuccessRate", "cleanSheetsDef", "cleanSheetsGK", "redCards",
)


# ---------- helpers ----------

def display_names(conn: sqlite3.Connection) -> dict:
    names = {}
    for row in conn.execute("SELECT gamertag, data_json FROM members"):
        names[row["gamertag"]] = json.loads(row["data_json"]).get("playerName") or row["gamertag"]
    return names


def _who(gamertag: str, names: dict) -> dict:
    return {"gamertag": gamertag, "displayName": names.get(gamertag, gamertag)}


def _player(member: dict) -> dict:
    tag = member["name"]
    out = {"gamertag": tag, "displayName": member.get("playerName") or tag}
    for f in PLAYER_FIELDS:
        out[f] = member.get(f)
    return out


def _members(conn) -> list:
    return [json.loads(r["data_json"]) for r in conn.execute("SELECT data_json FROM members")]


def _players_for(conn, match_ids: list) -> dict:
    by_match: dict = {mid: [] for mid in match_ids}
    if not match_ids:
        return by_match
    marks = ",".join("?" * len(match_ids))
    for row in conn.execute(f"SELECT * FROM match_players WHERE match_id IN ({marks})", match_ids):
        by_match[row["match_id"]].append(row)
    return by_match


def _match(row, players: list, names: dict) -> dict:
    motm_rows = [p for p in players if p["motm"]]
    motm = max(motm_rows, key=lambda p: p["rating"] or 0) if motm_rows else None
    best = max(players, key=lambda p: p["rating"] or 0) if players else None
    return {
        "matchId": row["match_id"],
        "timestamp": row["timestamp"],
        "opponentName": row["opponent_name"],
        "opponentCrestUrl": row["opponent_crest_url"],
        "goals": row["goals"],
        "goalsAgainst": row["goals_against"],
        "result": row["result"],
        "dnf": bool(row["dnf"]),
        "motm": _who(motm["gamertag"], names) if motm else None,
        "best": dict(_who(best["gamertag"], names), rating=best["rating"]) if best else None,
    }


def _matches(conn, rows, names) -> list:
    rows = list(rows)
    players = _players_for(conn, [r["match_id"] for r in rows])
    return [_match(r, players[r["match_id"]], names) for r in rows]


def _leader(players: list, field: str) -> Optional[dict]:
    if not players:
        return None
    top = max(players, key=lambda p: p.get(field) or 0)
    return {"gamertag": top["gamertag"], "displayName": top["displayName"], "value": top.get(field)}


def _latest_json(conn, column: str) -> dict:
    row = conn.execute(f"SELECT {column} FROM club_snapshots WHERE {column} IS NOT NULL "
                       "ORDER BY taken_at DESC, id DESC LIMIT 1").fetchone()
    return json.loads(row[0]) if row else {}


def _latest_snapshot(conn):
    return conn.execute("SELECT * FROM club_snapshots ORDER BY taken_at DESC, id DESC LIMIT 1").fetchone()


# ---------- routes ----------

def list_players(conn) -> list:
    players = [_player(m) for m in _members(conn)]
    return sorted(players, key=lambda p: (p["goals"] or 0), reverse=True)


def get_overview(conn) -> Optional[dict]:
    snap = _latest_snapshot(conn)
    if snap is None:
        return None
    # EA can briefly omit one part (e.g. the club is missing from the season search at a
    # season start): show the latest known value of each part instead of blanks.
    season = _latest_json(conn, "season_json")
    overall = _latest_json(conn, "overall_json")
    info_row = conn.execute("SELECT data_json FROM club_info WHERE id=1").fetchone()
    info = json.loads(info_row["data_json"]) if info_row else {}
    names = display_names(conn)

    recent = _matches(conn, conn.execute("SELECT * FROM matches ORDER BY timestamp DESC LIMIT 10"), names)
    mvp = Counter(m["motm"]["gamertag"] for m in recent if m["motm"])
    players = list_players(conn)

    return {
        "club": {
            "clubId": info.get("clubId") or season.get("clubId") or overall.get("clubId"),
            "name": info.get("clubName") or season.get("clubName") or "",
            "crestUrl": info.get("crestUrl") or season.get("crestUrl") or "",
            "stadium": info.get("stadium") or "",
            "division": season.get("currentDivision"),
            "bestDivision": overall.get("bestDivision") or season.get("bestDivision"),
            "promotions": overall.get("promotions"),
            "relegations": overall.get("relegations"),
            "skillRating": overall.get("skillRating"),
        },
        "season": {k: season.get(k) for k in ("gamesPlayed", "wins", "ties", "losses", "points", "goals", "goalsAgainst")},
        "allTime": {k: overall.get(k) for k in ("gamesPlayed", "wins", "ties", "losses", "goals", "goalsAgainst", "winStreak", "unbeatenStreak")},
        "recentMatches": recent,
        "mvpCounts": [dict(_who(tag, names), count=n) for tag, n in mvp.most_common()],
        "leaders": {
            "goals": _leader(players, "goals"),
            "assists": _leader(players, "assists"),
            "rating": _leader(players, "averageRating"),
        },
        "players": players,
        "updatedAt": snap["taken_at"],
    }


def get_player(conn, gamertag: str) -> Optional[dict]:
    row = conn.execute("SELECT data_json FROM members WHERE gamertag=?", (gamertag,)).fetchone()
    if row is None:
        return None
    history = [
        {"matchId": r["match_id"], "timestamp": r["timestamp"], "rating": r["rating"],
         "goals": r["goals"], "assists": r["assists"], "motm": bool(r["motm"])}
        for r in conn.execute(
            """SELECT p.*, m.timestamp FROM match_players p JOIN matches m USING (match_id)
               WHERE p.gamertag=? ORDER BY m.timestamp ASC""", (gamertag,))
    ]
    ratings = [h["rating"] for h in history if h["rating"] is not None]
    return {
        "player": _player(json.loads(row["data_json"])),
        "history": history,
        "tracked": {
            "games": len(history),
            "goals": sum(h["goals"] or 0 for h in history),
            "assists": sum(h["assists"] or 0 for h in history),
            "motm": sum(1 for h in history if h["motm"]),
            "avgRating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
        },
    }


SESSION_GAP = timedelta(hours=2)


def list_matches(conn, limit: int, before: Optional[str] = None) -> dict:
    """Newest `limit` matches older than `before`, extended so the oldest session is never split."""
    if before:
        rows = conn.execute("SELECT * FROM matches WHERE timestamp < ? ORDER BY timestamp DESC LIMIT ?", (before, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM matches ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()

    older = None
    while rows:
        older = conn.execute("SELECT * FROM matches WHERE timestamp < ? ORDER BY timestamp DESC LIMIT 1",
                             (rows[-1]["timestamp"],)).fetchone()
        if older is None:
            break
        gap = datetime.fromisoformat(rows[-1]["timestamp"]) - datetime.fromisoformat(older["timestamp"])
        if gap > SESSION_GAP:
            break
        rows.append(older)

    names = display_names(conn)
    return {
        "sessions": group_sessions(_matches(conn, rows, names), SESSION_GAP),
        "nextBefore": rows[-1]["timestamp"] if rows and older is not None else None,
    }


def get_match(conn, match_id: str) -> Optional[dict]:
    row = conn.execute("SELECT * FROM matches WHERE match_id=?", (match_id,)).fetchone()
    if row is None:
        return None
    names = display_names(conn)
    players = _players_for(conn, [match_id])[match_id]
    return {
        "match": _match(row, players, names),
        "players": [
            dict(_who(p["gamertag"], names), position=p["position"], rating=p["rating"], goals=p["goals"],
                 assists=p["assists"], shots=p["shots"], passesMade=p["passes_made"],
                 passAttempts=p["pass_attempts"], tacklesMade=p["tackles_made"],
                 tackleAttempts=p["tackle_attempts"], saves=p["saves"], manOfTheMatch=bool(p["motm"]),
                 secondsPlayed=p["seconds_played"])
            for p in sorted(players, key=lambda p: p["rating"] or 0, reverse=True)
        ],
    }


SEASON_TOTALS = ("gamesPlayed", "wins", "ties", "losses", "points", "goals", "goalsAgainst", "promotions", "relegations")


def get_seasons(conn) -> dict:
    snap_rows = conn.execute(
        """SELECT * FROM club_snapshots WHERE season_games IS NOT NULL AND division IS NOT NULL
           ORDER BY taken_at, id""").fetchall()
    season_json = {r["taken_at"]: json.loads(r["season_json"]) for r in snap_rows}
    snaps = [Snap(datetime.fromisoformat(r["taken_at"]), r["season_games"], r["division"],
                  r["season_promotions"] or 0, r["season_relegations"] or 0) for r in snap_rows]
    periods = detect_periods(snaps)
    if not periods:
        return {"eaSeasons": []}

    names = display_names(conn)
    match_rows = conn.execute("SELECT * FROM matches").fetchall()
    players = _players_for(conn, [r["match_id"] for r in match_rows])
    first_campaign = periods[0].campaigns[0]

    out = []
    for season in periods:
        campaigns = []
        for c in season.campaigns:
            lower = None if c is first_campaign else c.started_at
            in_range = [r for r in match_rows if _within(r["timestamp"], lower, c.ended_at)]
            campaigns.append(_campaign(c, in_range, players, names))
        totals = season_json.get(season.last_snap.taken_at.isoformat(), {})
        out.append({
            "startedAt": season.started_at.isoformat(),
            "endedAt": season.ended_at.isoformat() if season.ended_at else None,
            "partial": season.partial,
            "promotionsBeforeTracking": season.promotions_before_tracking,
            "totals": {k: totals.get(k) for k in SEASON_TOTALS},
            "campaigns": list(reversed(campaigns)),
        })
    return {"eaSeasons": list(reversed(out))}


def _within(ts: str, lower, upper) -> bool:
    when = datetime.fromisoformat(ts)
    return (lower is None or when >= lower) and (upper is None or when < upper)


def _campaign(c, rows, players, names) -> dict:
    results = [r["result"] for r in rows]
    goals, motm = Counter(), Counter()
    for r in rows:
        for p in players[r["match_id"]]:
            goals[p["gamertag"]] += p["goals"] or 0
            motm[p["gamertag"]] += 1 if p["motm"] else 0

    def top(counter):
        tag, value = max(counter.items(), key=lambda kv: kv[1], default=(None, 0))
        return dict(_who(tag, names), value=value) if tag and value > 0 else None

    return {
        "division": c.division,
        "startedAt": c.started_at.isoformat(),
        "endedAt": c.ended_at.isoformat() if c.ended_at else None,
        "outcome": c.outcome,
        "partial": c.partial,
        "wins": results.count("win"),
        "draws": results.count("draw"),
        "losses": results.count("loss"),
        "goals": sum(r["goals"] or 0 for r in rows),
        "goalsAgainst": sum(r["goals_against"] or 0 for r in rows),
        "topScorer": top(goals),
        "topMvp": top(motm),
    }


def get_status(conn) -> dict:
    row = conn.execute("SELECT * FROM collector_status WHERE id=1").fetchone()
    if row is None:
        return {"lastAttemptAt": None, "lastSuccessAt": None, "lastError": None}
    return {"lastAttemptAt": row["last_attempt_at"], "lastSuccessAt": row["last_success_at"], "lastError": row["last_error"]}
