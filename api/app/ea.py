"""Fetch everything the dashboard needs from EA in one go."""
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional, Protocol
from zoneinfo import ZoneInfo

from fc_clubs_api import FC27API

from app.config import Settings

LEAGUE = "leagueMatch"
MATCH_COUNT = 10


@dataclass
class Bundle:
    fetched_at: datetime
    season: Optional[dict]
    overall: Optional[dict]
    members: list
    matches: list
    match_players: list
    raw_matches: list
    details: Optional[dict]


class EASource(Protocol):
    def fetch(self, include_details: bool) -> Bundle: ...


class LiveEASource:
    def __init__(self, settings: Settings, sleep: Callable[[float], None] = time.sleep):
        self.settings = settings
        self.sleep = sleep
        self.api = FC27API(timezone=settings.tz)

    def fetch(self, include_details: bool) -> Bundle:
        cid = self.settings.club_id
        calls: list[Callable[[], object]] = [
            lambda: self.api.search_club_by_name(self.settings.club_name, scope="current_season"),
            lambda: self.api.get_club_overall_stats(cid),
            lambda: self.api.get_member_stats(cid),
            lambda: self.api.get_club_matches(cid, LEAGUE, MATCH_COUNT),
            lambda: self.api.get_club_matches(cid, LEAGUE, MATCH_COUNT, output="raw"),
            lambda: self.api.get_match_players(cid, LEAGUE, MATCH_COUNT),
        ]
        if include_details:
            calls.append(lambda: self.api.get_club_details(cid))

        results = []
        for i, call in enumerate(calls):
            if i:
                self.sleep(1)
            results.append(call())

        search, overall, members, matches, raw, players = results[:6]
        details = results[6] if include_details else None
        return Bundle(
            fetched_at=datetime.now(ZoneInfo(self.settings.tz)),
            season=next((r for r in (search or []) if int(r.get("clubId", 0)) == cid), None),
            overall=(overall or [None])[0],
            members=list(members or []),
            matches=list(matches or []),
            match_players=list(players or []),
            raw_matches=_raw_list(raw),
            details=(details or [None])[0] if include_details else None,
        )


def _raw_list(raw: object) -> list:
    """EA's raw matches payload is a list of match objects (or null)."""
    if isinstance(raw, list):
        return raw
    return []
