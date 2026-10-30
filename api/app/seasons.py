"""Infer EA seasons and division campaigns from club snapshots.

EA only exposes the current season's running totals, so boundaries are inferred:
- a new EA season starts when the season's games-played counter goes down (boundary =
  the last snapshot before the drop);
- a new division campaign starts when the current division changes
  (lower number = promoted, division 1 is the top).
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Snap:
    taken_at: datetime
    season_games: int
    division: int
    promotions: int
    relegations: int


@dataclass
class Campaign:
    division: int
    started_at: datetime
    ended_at: Optional[datetime]
    outcome: str
    partial: bool


@dataclass
class EASeason:
    started_at: datetime
    ended_at: Optional[datetime]
    partial: bool
    promotions_before_tracking: int
    campaigns: list = field(default_factory=list)
    last_snap: Optional[Snap] = None


def detect_periods(snaps: list) -> list:
    snaps = sorted(snaps, key=lambda s: s.taken_at)
    if not snaps:
        return []

    first = snaps[0]
    seasons = [EASeason(first.taken_at, None, True, first.promotions or 0,
                        [Campaign(first.division, first.taken_at, None, "in_progress", True)], first)]

    for prev, cur in zip(snaps, snaps[1:]):
        season = seasons[-1]
        if (cur.season_games or 0) < (prev.season_games or 0):
            # Matches after `prev` already belong to the new season (they produced cur's counts),
            # so the boundary is the last snapshot before the reset.
            _close(season.campaigns[-1], prev.taken_at, "stayed")
            season.ended_at = prev.taken_at
            seasons.append(EASeason(prev.taken_at, None, False, 0,
                                    [Campaign(cur.division, prev.taken_at, None, "in_progress", False)], cur))
            continue
        if cur.division != prev.division:
            outcome = "promoted" if cur.division < prev.division else "relegated"
            _close(season.campaigns[-1], cur.taken_at, outcome)
            season.campaigns.append(Campaign(cur.division, cur.taken_at, None, "in_progress", False))
        season.last_snap = cur

    return seasons


def _close(campaign: Campaign, at: datetime, outcome: str) -> None:
    campaign.ended_at = at
    campaign.outcome = outcome
