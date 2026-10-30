"""Test data built from Mind Eaters FC's real stats on 2026-10-30."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.ea import Bundle

SP = ZoneInfo("America/Sao_Paulo")
CREST = "https://example.test/crest.png"
T0 = datetime(2026, 10, 30, 12, 0, tzinfo=SP)


def t(hours: float) -> datetime:
    return T0 + timedelta(hours=hours)


def member(name, player_name, position, overall, gp, goals, assists, rating, motm, **kw):
    row = {
        "name": name, "playerName": player_name, "position": position, "overall": overall,
        "gamesPlayed": gp, "winRate": kw.get("winRate", 50), "goals": goals, "assists": assists,
        "averageRating": rating, "manOfTheMatch": motm, "shotSuccessRate": kw.get("shotSuccessRate", 40),
        "passesMade": kw.get("passesMade", 500), "passSuccessRate": kw.get("passSuccessRate", 75),
        "tacklesMade": kw.get("tacklesMade", 50), "tackleSuccessRate": kw.get("tackleSuccessRate", 40),
        "cleanSheetsDef": 0, "cleanSheetsGK": 0, "redCards": 0,
    }
    return row


MEMBERS = [
    member("netozeraaa", "Reginaldo", "midfielder", 82, 108, 117, 98, 8.2, 27, winRate=51, passSuccessRate=78, tackleSuccessRate=35),
    member("Baby2KK", "C. Carvalho", "forward", 79, 82, 88, 54, 7.8, 16, winRate=48),
    member("CUFIS", "A. Rufino", "forward", 83, 73, 58, 41, 7.6, 10, winRate=52),
    member("bielpontes04", "Path", "defender", 82, 59, 21, 46, 8.1, 15, winRate=59, passSuccessRate=83),
    member("6d9dd2e578c1d7a9", "J. Show", "defender", 83, 24, 2, 2, 6.4, 0, winRate=45),
]

PLAYER_IDS = {"netozeraaa": 1, "Baby2KK": 2, "CUFIS": 3, "bielpontes04": 4, "6d9dd2e578c1d7a9": 5}


def match(match_id, when, opponent, goals, against, dnf=False):
    result = "win" if goals > against else "loss" if goals < against else "draw"
    return {
        "matchId": int(match_id), "timestamp": when, "matchType": "leagueMatch", "clubId": 1232878,
        "clubName": "Mind Eaters FC", "opponentId": 900, "opponentName": opponent, "goals": goals,
        "goalsAgainst": against, "result": result, "dnf": dnf, "crestUrl": CREST, "opponentCrestUrl": CREST,
    }


def mp(match_id, when, gamertag, rating, goals=0, assists=0, motm=False, position="midfielder", seconds=5400):
    return {
        "matchId": int(match_id), "timestamp": when, "clubId": 1232878,
        "playerId": PLAYER_IDS.get(gamertag, 99), "name": gamertag, "position": position,
        "rating": rating, "goals": goals, "assists": assists, "shots": goals + 1,
        "passesMade": 20, "passAttempts": 25, "tacklesMade": 3, "tackleAttempts": 6, "saves": 0,
        "cleanSheet": 0, "manOfTheMatch": 1 if motm else 0, "redCards": 0, "secondsPlayed": seconds,
    }


MATCH_ID = "151090313490136"


def default_matches():
    m1 = match(MATCH_ID, t(-14), "Tamandua Xereka", 6, 3)
    m2 = match("151090313490100", t(-14.5), "bayern de mlks", 3, 3)
    m3 = match("151090313490050", t(-15), "PASSARALHOO FC", 2, 3)
    players = [
        mp(MATCH_ID, t(-14), "bielpontes04", 9.5, goals=1, assists=3, motm=True, position="defender"),
        mp(MATCH_ID, t(-14), "netozeraaa", 10.0),
        mp(MATCH_ID, t(-14), "Baby2KK", 8.9, goals=3, assists=1, position="forward"),
        mp("151090313490100", t(-14.5), "bielpontes04", 9.5, goals=1, assists=2, motm=True, position="defender"),
        mp("151090313490100", t(-14.5), "Baby2KK", 8.0, goals=2, assists=1, position="forward"),
        mp("151090313490050", t(-15), "bielpontes04", 8.6, goals=2, position="defender"),
        mp("151090313490050", t(-15), "CUFIS", 6.9, position="forward"),
    ]
    return [m1, m2, m3], players


def make_bundle(**overrides) -> Bundle:
    matches, players = default_matches()
    data = dict(
        fetched_at=T0,
        season={
            "clubId": 1232878, "clubName": "Mind Eaters FC", "currentDivision": 4, "bestDivision": 4,
            "gamesPlayed": 38, "wins": 19, "ties": 7, "losses": 12, "goals": 120, "goalsAgainst": 108,
            "cleanSheets": 3, "points": 28, "promotions": 2, "relegations": 0, "reputationTier": 1,
            "crestUrl": CREST,
        },
        overall={
            "clubId": 1232878, "gamesPlayed": 123, "wins": 63, "ties": 15, "losses": 45, "goals": 360,
            "goalsAgainst": 285, "skillRating": 1782, "winStreak": 1, "unbeatenStreak": 2,
            "promotions": 6, "relegations": 0, "bestDivision": 2, "reputationTier": 1,
        },
        members=[dict(m) for m in MEMBERS],
        matches=matches,
        match_players=players,
        raw_matches=[{"matchId": str(m["matchId"]), "raw": True} for m in matches],
        details={
            "clubId": 1232878, "clubName": "Mind Eaters FC", "regionId": 1, "teamId": 243,
            "crestAssetId": 99160915, "crestUrl": CREST, "stadium": "Estádio de ní",
        },
    )
    data.update(overrides)
    return Bundle(**data)


class FakeEASource:
    def __init__(self, items):
        self.items = list(items)
        self.calls = []

    def fetch(self, include_details: bool) -> Bundle:
        self.calls.append(include_details)
        item = self.items.pop(0)
        if isinstance(item, Exception):
            raise item
        return item
