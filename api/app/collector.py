"""Fetch from EA and save, on a timer. Never crashes the app."""
import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import Settings
from app.db import connect, init_schema
from app.ea import EASource
from app.store import save_bundle

log = logging.getLogger("mind_eaters.collector")
DETAILS_MAX_AGE = timedelta(hours=24)


def _details_due(conn: sqlite3.Connection, now: datetime) -> bool:
    row = conn.execute("SELECT updated_at FROM club_info WHERE id=1").fetchone()
    return row is None or now - datetime.fromisoformat(row[0]) >= DETAILS_MAX_AGE


def _set_status(conn, **fields) -> None:
    with conn:
        conn.execute("INSERT OR IGNORE INTO collector_status (id) VALUES (1)")
        for key, value in fields.items():
            conn.execute(f"UPDATE collector_status SET {key}=? WHERE id=1", (value,))


def collect_once(conn: sqlite3.Connection, source: EASource, now: datetime) -> bool:
    _set_status(conn, last_attempt_at=now.isoformat())
    try:
        bundle = source.fetch(include_details=_details_due(conn, now))
        save_bundle(conn, bundle)
    except Exception as e:  # EA is unofficial: any failure must leave saved data intact
        log.warning("collection failed: %s: %s", type(e).__name__, e)
        _set_status(conn, last_error=f"{type(e).__name__}: {e}")
        return False
    _set_status(conn, last_success_at=now.isoformat(), last_error=None)
    log.info("collection ok: %d matches, %d members", len(bundle.matches), len(bundle.members))
    return True


async def run_forever(settings: Settings, source: EASource) -> None:
    conn = connect(settings.db_path)
    init_schema(conn)
    tz = ZoneInfo(settings.tz)
    try:
        while True:
            await asyncio.to_thread(collect_once, conn, source, datetime.now(tz))
            await asyncio.sleep(settings.collect_interval_s)
    finally:
        conn.close()
