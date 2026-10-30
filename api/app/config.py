import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    club_id: int = 1232878
    club_name: str = "Mind Eaters FC"
    db_path: str = "/data/mind-eaters.db"
    collect_interval_s: int = 900
    collector_enabled: bool = True
    tz: str = "America/Sao_Paulo"


def _bool(value: str) -> bool:
    return value.strip().lower() not in ("0", "false", "no", "off", "")


def get_settings() -> Settings:
    d = Settings()
    env = os.environ
    return Settings(
        club_id=int(env.get("CLUB_ID", d.club_id)),
        club_name=env.get("CLUB_NAME", d.club_name),
        db_path=env.get("DB_PATH", d.db_path),
        collect_interval_s=int(env.get("COLLECT_INTERVAL_S", d.collect_interval_s)),
        collector_enabled=_bool(env.get("COLLECTOR_ENABLED", "true")),
        tz=env.get("TZ", d.tz),
    )
