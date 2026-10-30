from app.config import get_settings
from app.db import connect, init_schema


def test_init_schema_is_idempotent(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    init_schema(conn)
    init_schema(conn)
    names = {r[0] for r in conn.execute("select name from sqlite_master where type='table'")}
    assert {"matches", "match_players", "club_snapshots", "members", "club_info", "collector_status"} <= names


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("COLLECTOR_ENABLED", "false")
    monkeypatch.setenv("CLUB_ID", "42")
    s = get_settings()
    assert s.collector_enabled is False and s.club_id == 42 and s.tz == "America/Sao_Paulo"


def test_settings_defaults(monkeypatch):
    for k in ("CLUB_ID", "CLUB_NAME", "DB_PATH", "COLLECT_INTERVAL_S", "COLLECTOR_ENABLED", "TZ"):
        monkeypatch.delenv(k, raising=False)
    s = get_settings()
    assert (s.club_id, s.club_name, s.collect_interval_s, s.collector_enabled) == (1232878, "Mind Eaters FC", 900, True)
