"""EA's `archetypeid` (per player, per match) → archetype name, for FC 27 Clubs.

EA doesn't publish this list. Mapping from community research over ~835k player-games:
https://github.com/Interactive-63/eafc-pro-clubs-api-research/issues/5
IDs 7 (Recycler) and 9 (Creator) were inferred there and confirmed by our own squad.
Goalkeeper IDs are known to be goalkeepers but their exact archetype isn't, so they share one label.
If EA renumbers archetypes (e.g. after a title update), fix it here.
"""
from typing import Optional

ARCHETYPES = {
    1: "Goalkeeper",
    2: "Goalkeeper",
    3: "Progressor",
    4: "Boss",
    5: "Disruptor",
    6: "Marauder",
    7: "Recycler",
    8: "Maestro",
    9: "Creator",
    10: "Spark",
    11: "Magician",
    12: "Finisher",
    13: "Target Man",
    30: "Goalkeeper",
}


def archetype(archetype_id) -> Optional[dict]:
    """{"id", "name"} for an EA archetypeid, or None when EA didn't send one."""
    try:
        aid = int(archetype_id)
    except (TypeError, ValueError):
        return None
    return {"id": aid, "name": ARCHETYPES.get(aid, f"Archetype #{aid}")}
