"""Group matches into play sessions (a night of games)."""
from datetime import datetime, timedelta


def group_sessions(matches: list, gap: timedelta = timedelta(hours=2)) -> list:
    ordered = sorted(matches, key=lambda m: datetime.fromisoformat(m["timestamp"]))
    groups: list = []
    last = None
    for m in ordered:
        when = datetime.fromisoformat(m["timestamp"])
        if last is None or when - last > gap:
            groups.append([])
        groups[-1].append(m)
        last = when

    sessions = []
    for g in reversed(groups):
        results = [m["result"] for m in g]
        sessions.append({
            "start": g[0]["timestamp"],
            "wins": results.count("win"),
            "draws": results.count("draw"),
            "losses": results.count("loss"),
            "matches": list(reversed(g)),
        })
    return sessions
