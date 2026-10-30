import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS matches (
    match_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    match_type TEXT NOT NULL,
    opponent_id INTEGER,
    opponent_name TEXT,
    opponent_crest_url TEXT,
    goals INTEGER,
    goals_against INTEGER,
    result TEXT,
    dnf INTEGER,
    raw_json TEXT
);
CREATE INDEX IF NOT EXISTS matches_timestamp ON matches(timestamp);

CREATE TABLE IF NOT EXISTS match_players (
    match_id TEXT NOT NULL REFERENCES matches(match_id),
    player_id INTEGER NOT NULL,
    gamertag TEXT NOT NULL,
    position TEXT,
    rating REAL,
    goals INTEGER,
    assists INTEGER,
    shots INTEGER,
    passes_made INTEGER,
    pass_attempts INTEGER,
    tackles_made INTEGER,
    tackle_attempts INTEGER,
    saves INTEGER,
    clean_sheet INTEGER,
    motm INTEGER,
    red_cards INTEGER,
    seconds_played INTEGER,
    PRIMARY KEY (match_id, player_id)
);
CREATE INDEX IF NOT EXISTS match_players_gamertag ON match_players(gamertag);

CREATE TABLE IF NOT EXISTS club_snapshots (
    id INTEGER PRIMARY KEY,
    taken_at TEXT NOT NULL,
    season_json TEXT,
    overall_json TEXT,
    season_games INTEGER,
    division INTEGER,
    season_promotions INTEGER,
    season_relegations INTEGER
);

CREATE TABLE IF NOT EXISTS members (
    gamertag TEXT PRIMARY KEY,
    data_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS club_info (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    data_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS collector_status (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    last_attempt_at TEXT,
    last_success_at TEXT,
    last_error TEXT
);
"""


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
