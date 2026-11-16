"""Read models: turn stored rows into the JSON shapes of the API contract."""
import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from app.archetypes import ARCHETYPES, archetype
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


def _archetypes_for(conn, match_ids: Optional[list] = None) -> dict:
    """{(match_id, player_id): archetypeid} read from EA's raw match payload (it isn't in the parsed data)."""
    if match_ids is None:
        rows = conn.execute("SELECT match_id, raw_json FROM matches WHERE raw_json IS NOT NULL")
    elif not match_ids:
        return {}
    else:
        marks = ",".join("?" * len(match_ids))
        rows = conn.execute(f"SELECT match_id, raw_json FROM matches WHERE raw_json IS NOT NULL AND match_id IN ({marks})", match_ids)
    out = {}
    for row in rows:
        try:
            clubs = json.loads(row["raw_json"]).get("players") or {}
        except (ValueError, AttributeError):
            continue
        for players in clubs.values():
            for pid, p in (players or {}).items():
                if isinstance(p, dict) and p.get("archetypeid") is not None:
                    out[(row["match_id"], str(pid))] = p["archetypeid"]
    return out


def _archetype_of(archetypes: dict, row) -> Optional[dict]:
    return archetype(archetypes.get((row["match_id"], str(row["player_id"]))))


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

def _latest_archetypes(conn) -> dict:
    """Each player's archetype in their most recent saved match."""
    archetypes = _archetypes_for(conn)
    latest = {}
    for row in conn.execute(
            """SELECT p.match_id, p.player_id, p.gamertag FROM match_players p JOIN matches m USING (match_id)
               ORDER BY m.timestamp ASC"""):
        a = _archetype_of(archetypes, row)
        if a:
            latest[row["gamertag"]] = a
    return latest


def list_players(conn) -> list:
    latest = _latest_archetypes(conn)
    players = [dict(_player(m), archetype=latest.get(m["name"])) for m in _members(conn)]
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
    rows = conn.execute(
        """SELECT p.*, m.timestamp, m.result FROM match_players p JOIN matches m USING (match_id)
           WHERE p.gamertag=? ORDER BY m.timestamp ASC""", (gamertag,)).fetchall()
    archetypes = _archetypes_for(conn, [r["match_id"] for r in rows])
    history = [
        {"matchId": r["match_id"], "timestamp": r["timestamp"], "rating": r["rating"],
         "goals": r["goals"], "assists": r["assists"], "motm": bool(r["motm"]),
         "result": r["result"], "archetype": _archetype_of(archetypes, r)}
        for r in rows
    ]
    ratings = [h["rating"] for h in history if h["rating"] is not None]
    player = _player(json.loads(row["data_json"]))
    player["archetype"] = next((h["archetype"] for h in reversed(history) if h["archetype"]), None)
    return {
        "player": player,
        "history": history,
        "archetypes": _archetype_splits(history),
        "tracked": {
            "games": len(history),
            "goals": sum(h["goals"] or 0 for h in history),
            "assists": sum(h["assists"] or 0 for h in history),
            "motm": sum(1 for h in history if h["motm"]),
            "avgRating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
        },
    }


def _record(hs: list) -> dict:
    """W/D/L, output and average rating over a player's games (oldest first)."""
    ratings = [h["rating"] for h in hs if h["rating"] is not None]
    return dict(
        games=len(hs),
        wins=sum(h["result"] == "win" for h in hs), draws=sum(h["result"] == "draw" for h in hs),
        losses=sum(h["result"] == "loss" for h in hs),
        goals=sum(h["goals"] or 0 for h in hs), assists=sum(h["assists"] or 0 for h in hs),
        motm=sum(1 for h in hs if h["motm"]),
        avgRating=round(sum(ratings) / len(ratings), 2) if ratings else None,
        lastPlayed=hs[-1]["timestamp"],
    )


def _archetype_splits(history: list) -> list:
    """A player's record with each archetype they've used, most-played first."""
    groups: dict = {}
    for h in history:
        if h["archetype"]:
            groups.setdefault(h["archetype"]["id"], []).append(h)
    out = [dict(hs[0]["archetype"], **_record(hs)) for hs in groups.values()]
    return sorted(out, key=lambda a: a["games"], reverse=True)


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
    archetypes = _archetypes_for(conn, [match_id])
    return {
        "match": _match(row, players, names),
        "players": [
            dict(_who(p["gamertag"], names), position=p["position"], rating=p["rating"], goals=p["goals"],
                 assists=p["assists"], shots=p["shots"], passesMade=p["passes_made"],
                 passAttempts=p["pass_attempts"], tacklesMade=p["tackles_made"],
                 tackleAttempts=p["tackle_attempts"], saves=p["saves"], manOfTheMatch=bool(p["motm"]),
                 secondsPlayed=p["seconds_played"], archetype=_archetype_of(archetypes, p))
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


# ---------- time of day ----------

TIME_SLOTS = (("morning", "Morning", 6, 12), ("afternoon", "Afternoon", 12, 18), ("night", "Night", 18, 6))


def _slot(hour: int) -> str:
    for key, _, start, end in TIME_SLOTS:
        if (start <= hour < end) if start < end else (hour >= start or hour < end):
            return key
    raise ValueError(hour)


def get_time_of_day(conn, tz: str = "America/Sao_Paulo") -> dict:
    """Win/draw/loss record of every tracked match, grouped by the local hour it was played."""
    zone = ZoneInfo(tz)
    counts = {key: Counter() for key, *_ in TIME_SLOTS}
    for row in conn.execute("SELECT timestamp, result FROM matches"):
        hour = datetime.fromisoformat(row["timestamp"]).astimezone(zone).hour
        counts[_slot(hour)][row["result"]] += 1
    slots = []
    for key, label, start, end in TIME_SLOTS:
        c = counts[key]
        games = c["win"] + c["draw"] + c["loss"]
        slots.append({
            "slot": key, "label": label, "startHour": start, "endHour": end,
            "games": games, "wins": c["win"], "draws": c["draw"], "losses": c["loss"],
            "winRate": round(c["win"] / games * 100) if games else 0,
        })
    return {"slots": slots}


# ---------- opponents ----------

def list_opponents(conn) -> list:
    """Every club we've played, with our head-to-head record, most-played first."""
    names = display_names(conn)
    rows = conn.execute("SELECT * FROM matches ORDER BY timestamp DESC").fetchall()
    matches = _matches(conn, rows, names)
    by_club: dict = {}
    for row, m in zip(rows, matches):
        key = row["opponent_id"] if row["opponent_id"] is not None else f"name:{row['opponent_name']}"
        by_club.setdefault(key, []).append(m)
    out = []
    for key, ms in by_club.items():
        latest = ms[0]  # rows are newest first, so this carries the club's current name/crest
        out.append({
            "opponentId": None if isinstance(key, str) else key,
            "name": latest["opponentName"],
            "crestUrl": latest["opponentCrestUrl"],
            "games": len(ms),
            "wins": sum(m["result"] == "win" for m in ms),
            "draws": sum(m["result"] == "draw" for m in ms),
            "losses": sum(m["result"] == "loss" for m in ms),
            "goals": sum(m["goals"] or 0 for m in ms),
            "goalsAgainst": sum(m["goalsAgainst"] or 0 for m in ms),
            "lastPlayed": latest["timestamp"],
            "matches": ms,
        })
    out.sort(key=lambda o: o["lastPlayed"], reverse=True)
    out.sort(key=lambda o: o["games"], reverse=True)
    return out


# ---------- archetypes ----------

def get_archetypes(conn) -> dict:
    """Each archetype we've used: team record in matches where one of us played it, and every player's numbers in it."""
    names = display_names(conn)
    archetypes = _archetypes_for(conn)
    acc: dict = {}
    for p in conn.execute(
            """SELECT p.*, m.timestamp, m.result FROM match_players p JOIN matches m USING (match_id)
               ORDER BY m.timestamp ASC"""):
        a = _archetype_of(archetypes, p)
        if a is None:
            continue
        g = acc.setdefault(a["id"], {"archetype": a, "results": {}, "players": {}})
        g["results"][p["match_id"]] = p["result"]
        g["players"].setdefault(p["gamertag"], []).append({
            "result": p["result"], "goals": p["goals"], "assists": p["assists"], "motm": bool(p["motm"]),
            "rating": p["rating"], "timestamp": p["timestamp"],
        })

    out = []
    for g in acc.values():
        res = Counter(g["results"].values())
        games = len(g["results"])
        rows = [r for hs in g["players"].values() for r in hs]
        ratings = [r["rating"] for r in rows if r["rating"] is not None]
        players = [dict(_who(tag, names), **_record(hs)) for tag, hs in g["players"].items()]
        players.sort(key=lambda x: (x["games"], x["goals"]), reverse=True)
        out.append(dict(
            g["archetype"], games=games, wins=res["win"], draws=res["draw"], losses=res["loss"],
            winRate=round(res["win"] / games * 100) if games else 0,
            playerGames=len(rows), goals=sum(r["goals"] or 0 for r in rows),
            assists=sum(r["assists"] or 0 for r in rows), motm=sum(r["motm"] for r in rows),
            avgRating=round(sum(ratings) / len(ratings), 2) if ratings else None,
            players=players,
        ))
    out.sort(key=lambda a: a["games"], reverse=True)
    used = {a["name"] for a in out}
    unused = sorted({n for n in ARCHETYPES.values() if n not in used})
    return {"archetypes": out, "unused": unused}
