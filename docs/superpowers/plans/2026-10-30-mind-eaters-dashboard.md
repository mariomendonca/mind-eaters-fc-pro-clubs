# Mind Eaters FC Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A public dashboard at `https://mindeatersfc.mariomendonca.dev` showing Mind Eaters FC's club, player, match and season stats, and saving EA's data every 15 minutes so history builds up from 2026-10-30.

**Architecture:** A Python FastAPI service (`api/`) wraps `fc-clubs-api`, runs a background collector that writes to SQLite, derives sessions, EA seasons and division campaigns, and serves JSON under `/api/*`. A Vite + React SPA (`web/`) renders it in the approved purple/green look and is served by nginx. Both ship as GHCR images and deploy through the existing `personal-vps-infra` pattern behind Caddy.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, `fc-clubs-api==0.3.0`, sqlite3 (stdlib), pytest + httpx · Node 22, Vite, React 18, TypeScript, react-router-dom 6, Vitest + Testing Library · Docker, nginx, GitHub Actions, Caddy.

**Spec:** `docs/superpowers/specs/2026-10-30-mind-eaters-dashboard-design.md`
**Visual reference:** `docs/design/look-v1.html` (copy its CSS tokens, fonts and component styles; it is the approved look)

## Global Constraints

- Club ID `1232878`, club name `Mind Eaters FC`, platform `common-gen5` (library default).
- Display/grouping timezone `America/Sao_Paulo`.
- Collection every 900 s; at most ~6 EA calls per run, 1 s apart; club details at most once per 24 h.
- Pin `fc-clubs-api==0.3.0`.
- Colors: `--purple:#8b3dff`, `--green:#39ff88`, ink `#0b0812`; fonts Big Shoulders Display / Familjen Grotesk / Martian Mono.
- Player key = gamertag (`name` in EA rows); display = `playerName` from member stats, falling back to gamertag.
- Division 1 is top, 6 is bottom: a lower number means promoted.
- First EA season and first campaign are labeled "since tracking started" (`partial: true`). Never invent pre-tracking campaigns.
- Public site, `X-Robots-Tag: noindex, nofollow`, no auth.
- `matchId` is serialized as a **string** in JSON.
- Container names `mind-eaters-api` (port 8000) and `mind-eaters-web` (port 80); volume `mind_eaters_data`; images `ghcr.io/mariomendonca/mind-eaters-api|web:<sha>`.

## Review Focus

1. **EA down or slow during a collection run** → the run records `lastError`, saved data keeps being served, and the UI shows "last updated X ago". *(Task 6 test `test_collect_failure_keeps_data`.)*
2. **First boot with an empty database** → `/api/overview` returns 503 `{"detail":"no data yet"}` and the web app shows "Collecting the first data from EA…" instead of crashing. *(Tasks 6 and 8.)*
3. **A match player who has left the club** (not in member stats) → shows the gamertag as their name, with no crash. *(Task 5 test `test_display_name_falls_back_to_gamertag`.)*
4. **The same 10 matches fetched on every run** → no duplicate matches or player rows. *(Task 3 test `test_save_is_idempotent`.)*
5. **EA returns `null`/`[]` for matches, or a match with no MOTM** → treated as no matches / `motm: null`, and the UI shows "no MOTM". *(Task 2 test `test_null_matches_become_empty`, Task 5 test `test_match_without_motm`.)*

---

## File Structure

```
mind-eaters-fc/
  .gitignore                      # .superpowers/, node_modules, __pycache__, *.db, dist
  api/
    pyproject.toml
    Dockerfile
    app/
      config.py                   # Settings from env
      db.py                       # connect(), init_schema()
      ea.py                       # Bundle dataclass, EASource protocol, LiveEASource
      store.py                    # save_bundle()
      seasons.py                  # detect_periods() — EA seasons + campaigns (pure)
      sessions.py                 # group_sessions() (pure)
      queries.py                  # read models used by routes
      collector.py                # collect_once(), run_forever()
      main.py                     # FastAPI app, routes, lifespan
    tests/
      conftest.py                 # tmp db, FakeEASource, sample bundle builder
      test_ea.py test_store.py test_seasons.py test_sessions.py test_queries.py test_api.py
  web/
    package.json vite.config.ts tsconfig.json index.html Dockerfile nginx.conf
    src/
      main.tsx App.tsx            # router + layout (header + tabs)
      api.ts types.ts             # fetch helpers + response types (mirror API contract)
      theme.css                   # tokens + shared styles lifted from look-v1.html
      format.ts                   # dates in America/Sao_Paulo, "x ago"
      components/  Header.tsx Tabs.tsx StatStrip.tsx FormStrip.tsx MatchRow.tsx
                   PlayerCard.tsx Leaders.tsx MvpBars.tsx Sparkline.tsx StateMessage.tsx
      pages/       Overview.tsx Players.tsx PlayerPage.tsx Matches.tsx Seasons.tsx
      __tests__/   *.test.tsx
  .github/workflows/deploy.yml
personal-vps-infra/ (separate repo)
  mind-eaters/docker-compose.prod.yml, mind-eaters/.env.production.example
  .github/workflows/deploy-mind-eaters.yml
  proxy/Caddyfile (new block), README.md (new section)
```

## API Contract (shared by Tasks 5–11)

Types are in TypeScript notation; `web/src/types.ts` mirrors them exactly.

```ts
type Who = { gamertag: string; displayName: string };
type Match = { matchId: string; timestamp: string /* ISO, -03:00 */; opponentName: string;
  opponentCrestUrl: string; goals: number; goalsAgainst: number;
  result: "win" | "draw" | "loss"; dnf: boolean;
  motm: Who | null; best: (Who & { rating: number }) | null };
type Player = Who & { position: string; overall: number; gamesPlayed: number; winRate: number;
  goals: number; assists: number; averageRating: number; manOfTheMatch: number;
  shotSuccessRate: number; passesMade: number; passSuccessRate: number; tacklesMade: number;
  tackleSuccessRate: number; cleanSheetsDef: number; cleanSheetsGK: number; redCards: number };
type MatchPlayer = Who & { position: string; rating: number; goals: number; assists: number;
  shots: number; passesMade: number; passAttempts: number; tacklesMade: number;
  tackleAttempts: number; saves: number; manOfTheMatch: boolean; secondsPlayed: number };
type Leader = (Who & { value: number }) | null;

GET /api/health   -> { status: "ok" }                                   // always 200
GET /api/status   -> { lastAttemptAt: string|null; lastSuccessAt: string|null; lastError: string|null }
GET /api/overview -> 503 {detail:"no data yet"} | {
  club: { clubId: number; name: string; crestUrl: string; stadium: string; division: number;
          bestDivision: number; promotions: number; relegations: number; skillRating: number };
  season: { gamesPlayed; wins; ties; losses; points; goals; goalsAgainst: number };
  allTime: { gamesPlayed; wins; ties; losses; goals; goalsAgainst; winStreak; unbeatenStreak: number };
  recentMatches: Match[];              // newest first, max 10
  mvpCounts: (Who & { count: number })[]; // over recentMatches, desc, only count>0
  leaders: { goals: Leader; assists: Leader; rating: Leader };  // from member stats
  players: Player[];                   // sorted by goals desc
  updatedAt: string }
GET /api/players               -> Player[]
GET /api/players/{gamertag}    -> 404 | { player: Player;
  history: { matchId: string; timestamp: string; rating: number; goals: number; assists: number; motm: boolean }[]; // oldest first
  tracked: { games: number; goals: number; assists: number; motm: number; avgRating: number } }
GET /api/matches?limit=50      -> { sessions: { start: string; wins: number; draws: number; losses: number; matches: Match[] }[] } // newest first
GET /api/matches/{matchId}     -> 404 | { match: Match; players: MatchPlayer[] }  // players by rating desc
GET /api/seasons -> { eaSeasons: { startedAt: string; endedAt: string|null; partial: boolean;
    promotionsBeforeTracking: number;
    totals: { gamesPlayed; wins; ties; losses; points; goals; goalsAgainst; promotions; relegations: number };
    campaigns: { division: number; startedAt: string; endedAt: string|null;
      outcome: "promoted"|"relegated"|"stayed"|"in_progress"; partial: boolean;
      wins; draws; losses; goals; goalsAgainst: number; topScorer: Leader; topMvp: Leader }[] // newest first
  }[] }  // newest first
```

---

### Task 1: Repo scaffold, settings and database schema

**Files:**
- Create: `api/pyproject.toml`, `api/app/__init__.py`, `api/app/config.py`, `api/app/db.py`, `api/tests/conftest.py`, `api/tests/test_db.py`

**Interfaces:**
- Produces: `Settings` dataclass with `club_id: int = 1232878`, `club_name: str = "Mind Eaters FC"`, `db_path: str = "/data/mind-eaters.db"`, `collect_interval_s: int = 900`, `collector_enabled: bool = True`, `tz: str = "America/Sao_Paulo"`, loaded by `get_settings() -> Settings` from env vars `CLUB_ID, CLUB_NAME, DB_PATH, COLLECT_INTERVAL_S, COLLECTOR_ENABLED, TZ`.
- Produces: `connect(db_path: str) -> sqlite3.Connection` (row_factory = `sqlite3.Row`, WAL, foreign keys on) and `init_schema(conn) -> None` (idempotent).
- Schema (tables later tasks rely on):
  - `matches(match_id TEXT PK, timestamp TEXT, match_type TEXT, opponent_id INTEGER, opponent_name TEXT, opponent_crest_url TEXT, goals INTEGER, goals_against INTEGER, result TEXT, dnf INTEGER, raw_json TEXT)`
  - `match_players(match_id TEXT, player_id INTEGER, gamertag TEXT, position TEXT, rating REAL, goals INTEGER, assists INTEGER, shots INTEGER, passes_made INTEGER, pass_attempts INTEGER, tackles_made INTEGER, tackle_attempts INTEGER, saves INTEGER, clean_sheet INTEGER, motm INTEGER, red_cards INTEGER, seconds_played INTEGER, PRIMARY KEY(match_id, player_id))`
  - `club_snapshots(id INTEGER PK, taken_at TEXT, season_json TEXT, overall_json TEXT, season_games INTEGER, division INTEGER, season_promotions INTEGER, season_relegations INTEGER)`
  - `members(gamertag TEXT PK, data_json TEXT, updated_at TEXT)` (latest member stats)
  - `club_info(id INTEGER PK CHECK(id=1), data_json TEXT, updated_at TEXT)`
  - `collector_status(id INTEGER PK CHECK(id=1), last_attempt_at TEXT, last_success_at TEXT, last_error TEXT)`

- [ ] **Step 1:** The git repo already exists (GitHub `mariomendonca/mind-eaters-fc-pro-clubs`, local folder `mind-eaters-fc/`, `.gitignore` committed). Create `api/pyproject.toml` with deps `fastapi`, `uvicorn[standard]`, `fc-clubs-api==0.3.0` and dev extras `pytest`, `httpx`; set `[tool.pytest.ini_options] pythonpath=["."]`. Create venv: `cd api && python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"`.
- [ ] **Step 2: Write the failing test** `tests/test_db.py`:

```python
def test_init_schema_is_idempotent(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    init_schema(conn); init_schema(conn)
    names = {r[0] for r in conn.execute("select name from sqlite_master where type='table'")}
    assert {"matches","match_players","club_snapshots","members","club_info","collector_status"} <= names

def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("COLLECTOR_ENABLED", "false"); monkeypatch.setenv("CLUB_ID", "42")
    s = get_settings()
    assert s.collector_enabled is False and s.club_id == 42 and s.tz == "America/Sao_Paulo"
```

`conftest.py` provides a `conn` fixture (tmp db, schema initialized).
- [ ] **Step 3:** Run `cd api && .venv/bin/pytest tests/test_db.py -v` → FAIL (import error).
- [ ] **Step 4:** Implement `config.py` and `db.py` per Interfaces.
- [ ] **Step 5:** Run the tests again → PASS.
- [ ] **Step 6:** Commit `chore: scaffold api with settings and sqlite schema`.

---

### Task 2: EA source adapter

**Files:**
- Create: `api/app/ea.py`, `api/tests/test_ea.py`; extend `api/tests/conftest.py`

**Interfaces:**
- Produces:

```python
@dataclass
class Bundle:
    fetched_at: datetime                 # tz-aware
    season: dict | None                  # current_season search row for our club (records format)
    overall: dict | None                 # get_club_overall_stats()[0]
    members: list[dict]                  # get_member_stats()
    matches: list[dict]                  # get_club_matches(leagueMatch, 10), [] if EA gives null
    match_players: list[dict]            # get_match_players(leagueMatch, 10)
    raw_matches: list[dict]              # get_club_matches(..., output="raw") or [] — stored per match
    details: dict | None                 # get_club_details()[0] when requested, else None

class EASource(Protocol):
    def fetch(self, include_details: bool) -> Bundle: ...

class LiveEASource:                      # wraps FC27API(timezone=settings.tz)
    def __init__(self, settings: Settings, sleep=time.sleep): ...
    def fetch(self, include_details: bool) -> Bundle: ...
```

- `LiveEASource.fetch` calls the library in this order with `sleep(1)` between calls: season search (`scope="current_season"`, pick the row whose `clubId == settings.club_id`), overall, members, matches (records), raw matches, match players, and details if requested. Any `FC27APIError` propagates (the collector handles it).
- `conftest.py` gains `FakeEASource(bundles: list[Bundle])` (returns them in order, raises if a list item is an Exception) and `make_bundle(**overrides) -> Bundle` built from the real 2026-10-30 values in spec §3 (e.g. season 38 GP 19W 7D 12L 28 pts division 4 promotions 2; overall 123 GP skillRating 1782; members including `netozeraaa`/`Reginaldo` MID 117 G 98 A 8.2 MOTM 27 and `bielpontes04`/`Path`; one match `151090313490136` win 6–3 vs "Tamandua Xereka" with `bielpontes04` as MOTM).

- [ ] **Step 1: Write the failing tests** using a stub `FC27API` injected via monkeypatch:

```python
def test_fetch_picks_our_club_from_season_search(stub_api): ...
    # search returns [other club, ours] -> bundle.season["clubId"] == 1232878
def test_null_matches_become_empty(stub_api): ...
    # stub get_club_matches returns None -> bundle.matches == [] and bundle.match_players == []
def test_sleeps_between_calls(stub_api):
    sleeps = []; LiveEASource(settings, sleep=sleeps.append).fetch(include_details=False)
    assert len(sleeps) >= 5 and all(s == 1 for s in sleeps)
def test_details_only_when_requested(stub_api): ...  # details is None vs dict
```

- [ ] **Step 2:** Run `pytest tests/test_ea.py -v` → FAIL.
- [ ] **Step 3:** Implement `ea.py`.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(api): EA source adapter returning a Bundle`.

---

### Task 3: Saving a bundle

**Files:**
- Create: `api/app/store.py`, `api/tests/test_store.py`

**Interfaces:**
- Consumes: `Bundle`, `connect/init_schema`, `make_bundle`.
- Produces: `save_bundle(conn, bundle: Bundle) -> None` — upserts matches (`INSERT OR IGNORE` on `match_id`; `raw_json` from the raw match whose `matchId` matches), upserts match_players (`INSERT OR REPLACE` on PK), inserts one `club_snapshots` row when `season` or `overall` is present (`season_games`, `division=season["currentDivision"]`, `season_promotions`, `season_relegations` pulled from the season row), replaces `members` rows (members not in the bundle are kept: they may have left, and history still references them), and upserts `club_info` when `details` is present. All in one transaction.

- [ ] **Step 1: Write the failing tests:**

```python
def test_save_is_idempotent(conn):
    b = make_bundle(); save_bundle(conn, b); save_bundle(conn, b)
    assert conn.execute("select count(*) from matches").fetchone()[0] == len(b.matches)
    assert conn.execute("select count(*) from match_players").fetchone()[0] == len(b.match_players)
    assert conn.execute("select count(*) from club_snapshots").fetchone()[0] == 2

def test_snapshot_columns(conn):
    save_bundle(conn, make_bundle())
    row = conn.execute("select season_games, division, season_promotions from club_snapshots").fetchone()
    assert tuple(row) == (38, 4, 2)

def test_departed_member_kept(conn):
    save_bundle(conn, make_bundle())
    save_bundle(conn, make_bundle(members=[m for m in make_bundle().members if m["name"] != "bielpontes04"]))
    assert conn.execute("select 1 from members where gamertag='bielpontes04'").fetchone()
```

- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(api): idempotent bundle storage`.

---

### Task 4: EA seasons and division campaigns

**Files:**
- Create: `api/app/seasons.py`, `api/tests/test_seasons.py`

**Interfaces:**
- Produces (pure, no DB):

```python
@dataclass
class Snap:  taken_at: datetime; season_games: int; division: int; promotions: int; relegations: int
@dataclass
class Campaign: division: int; started_at: datetime; ended_at: datetime | None; outcome: str; partial: bool
@dataclass
class EASeason: started_at: datetime; ended_at: datetime | None; partial: bool
                promotions_before_tracking: int; campaigns: list[Campaign]; last_snap: Snap
def detect_periods(snaps: list[Snap]) -> list[EASeason]   # snaps sorted by taken_at; result oldest first
```

- Rules (from spec §5.3):
  - A new EA season starts at snap *i* when `season_games[i] < season_games[i-1]`. The previous season ends at `snaps[i].taken_at`, and its last campaign gets `outcome="stayed"`.
  - Within a season, a new campaign starts at snap *i* when `division[i] != division[i-1]`. The previous campaign ends at `snaps[i].taken_at` with `outcome = "promoted" if division[i] < division[i-1] else "relegated"`.
  - The newest campaign of the newest season has `ended_at=None` and `outcome="in_progress"`.
  - The very first season and its first campaign have `partial=True`. That season's `promotions_before_tracking = snaps[0].promotions`. Seasons that start after tracking began have `partial=False` and `promotions_before_tracking=0`.
  - `started_at` of the first season/campaign = `snaps[0].taken_at`.

- [ ] **Step 1: Write the failing tests** (times as `t(n)` = 2026-10-30 + n hours):

```python
def test_single_snapshot_is_partial_in_progress():
    [s] = detect_periods([Snap(t(0), 38, 4, 2, 0)])
    assert s.partial and s.promotions_before_tracking == 2
    assert [(c.division, c.outcome, c.partial) for c in s.campaigns] == [(4, "in_progress", True)]

def test_promotion_starts_new_campaign():
    [s] = detect_periods([Snap(t(0),38,4,2,0), Snap(t(1),45,4,2,0), Snap(t(2),48,3,3,0)])
    assert [(c.division, c.outcome) for c in s.campaigns] == [(4,"promoted"), (3,"in_progress")]
    assert s.campaigns[0].ended_at == t(2) and s.campaigns[1].partial is False

def test_relegation():
    [s] = detect_periods([Snap(t(0),10,3,0,0), Snap(t(1),20,4,0,1)])
    assert s.campaigns[0].outcome == "relegated"

def test_games_drop_starts_new_season():
    a, b = detect_periods([Snap(t(0),60,2,4,0), Snap(t(5),2,2,0,0)])
    assert a.ended_at == t(5) and a.campaigns[-1].outcome == "stayed"
    assert b.partial is False and b.promotions_before_tracking == 0
    assert b.campaigns[0].outcome == "in_progress"

def test_empty_input():
    assert detect_periods([]) == []
```

- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(api): detect EA seasons and division campaigns`.

---

### Task 5: Sessions and read models

**Files:**
- Create: `api/app/sessions.py`, `api/app/queries.py`, `api/tests/test_sessions.py`, `api/tests/test_queries.py`

**Interfaces:**
- Consumes: DB tables (Task 1), `save_bundle` (for test setup), `detect_periods`, `Snap`.
- Produces:
  - `group_sessions(matches: list[dict], gap: timedelta = timedelta(hours=2)) -> list[dict]`: input is Match dicts (any order). Output is newest-first sessions `{start, wins, draws, losses, matches}`, with matches newest first. A new session starts when the gap between consecutive matches (oldest to newest) is more than `gap`.
  - In `queries.py`, each function returns the exact JSON shapes in the API Contract (camelCase keys):
    `get_overview(conn) -> dict | None` (None when no snapshot exists),
    `list_players(conn) -> list[dict]`, `get_player(conn, gamertag) -> dict | None`,
    `list_matches(conn, limit: int) -> dict`, `get_match(conn, match_id: str) -> dict | None`,
    `get_seasons(conn) -> dict`, `get_status(conn) -> dict`.
  - `display_names(conn) -> dict[str, str]` maps gamertag to playerName from `members`; callers fall back to the gamertag.
  - `Match.motm` is the player row with `motm=1` (if several, the highest rating), else `None`. `Match.best` is the highest-rated player row.
  - `get_seasons` builds `Snap`s from `club_snapshots`, runs `detect_periods`, and computes per-campaign W/D/L, goals, `topScorer` (most goals) and `topMvp` (most MOTM) from matches whose timestamp is in `[started_at, ended_at)`. The first campaign has no lower bound (tracking began with EA's last 10 matches). EA-season `totals` come from the season's `last_snap` `season_json`.

- [ ] **Step 1: Write the failing tests:**

```python
def test_sessions_split_on_gap():
    ms = [m("1", t(0)), m("2", t(0.5)), m("3", t(5))]
    s = group_sessions(ms)
    assert [[x["matchId"] for x in g["matches"]] for g in s] == [["3"], ["2", "1"]]

def test_session_counts():  # 2 wins + 1 loss in one session -> wins=2, losses=1

def test_overview_none_when_empty(conn): assert get_overview(conn) is None

def test_overview_shape(conn):
    save_bundle(conn, make_bundle())
    o = get_overview(conn)
    assert o["club"]["skillRating"] == 1782 and o["season"]["points"] == 28
    assert o["recentMatches"][0]["matchId"] == "151090313490136"
    assert o["recentMatches"][0]["motm"] == {"gamertag": "bielpontes04", "displayName": "Path"}
    assert o["leaders"]["goals"]["displayName"] == "Reginaldo" and o["leaders"]["goals"]["value"] == 117

def test_match_without_motm(conn):   # bundle where no player has manOfTheMatch -> motm is None, best is set

def test_display_name_falls_back_to_gamertag(conn):
    # match_players contains gamertag "ghost99" absent from members
    assert any(p["displayName"] == "ghost99" for p in get_match(conn, mid)["players"])

def test_player_history_oldest_first(conn): ...
def test_get_player_unknown_returns_none(conn): assert get_player(conn, "nope") is None
def test_seasons_partial_first(conn):
    save_bundle(conn, make_bundle())
    [s] = get_seasons(conn)["eaSeasons"]
    assert s["partial"] and s["promotionsBeforeTracking"] == 2 and s["campaigns"][0]["outcome"] == "in_progress"
```

- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(api): sessions and read models`.

---

### Task 6: Collector and HTTP routes

**Files:**
- Create: `api/app/collector.py`, `api/app/main.py`, `api/tests/test_api.py`, `api/Dockerfile`

**Interfaces:**
- Consumes: `EASource`, `save_bundle`, `queries.*`, `Settings`.
- Produces:
  - `collect_once(conn, source: EASource, now: datetime) -> bool`. Sets `last_attempt_at`. Fetches with `include_details` = (no `club_info` row, or its `updated_at` is older than 24 h). On success it saves, sets `last_success_at` and clears `last_error`. On any exception it stores `f"{type(e).__name__}: {e}"` in `last_error`, logs it, and returns False (it never raises).
  - `run_forever(settings, source)`: an async loop that calls `collect_once` via `asyncio.to_thread`, then sleeps `collect_interval_s`.
  - `create_app(settings: Settings | None = None, source: EASource | None = None) -> FastAPI`. The lifespan opens the DB and runs `init_schema`. If `collector_enabled`, it starts `run_forever` as a task (first run immediately) and cancels it on shutdown. Routes follow the API Contract, all under `/api`. `/api/overview` returns 503 `{"detail":"no data yet"}` when `get_overview` is None, and the 404s are as listed. `app = create_app()` sits at module level for uvicorn.
- Dockerfile: `python:3.12-slim`, non-root user, `pip install .`, `VOLUME /data`, `EXPOSE 8000`, `CMD uvicorn app.main:app --host 0.0.0.0 --port 8000`, and `HEALTHCHECK` with python urllib on `http://127.0.0.1:8000/api/health`.

- [ ] **Step 1: Write the failing tests** (TestClient with `COLLECTOR_ENABLED=false` and a tmp DB):

```python
def test_health(client): assert client.get("/api/health").json() == {"status": "ok"}
def test_overview_503_when_empty(client):
    r = client.get("/api/overview"); assert r.status_code == 503 and r.json()["detail"] == "no data yet"
def test_collect_then_overview(conn, client):
    assert collect_once(conn, FakeEASource([make_bundle()]), now=t(0)) is True
    assert client.get("/api/overview").json()["club"]["name"] == "Mind Eaters FC"
def test_collect_failure_keeps_data(conn, client):
    collect_once(conn, FakeEASource([make_bundle()]), now=t(0))
    assert collect_once(conn, FakeEASource([FC27HTTPError(403)]), now=t(1)) is False
    st = client.get("/api/status").json()
    assert st["lastError"].startswith("FC27HTTPError") and st["lastSuccessAt"] is not None
    assert client.get("/api/overview").status_code == 200
def test_details_refetched_daily(conn): ...  # include_details True on first run, False 1h later, True 25h later
def test_unknown_match_404(client): assert client.get("/api/matches/1").status_code == 404
def test_match_id_is_string(conn, client): ...
```

(Build `FC27HTTPError` the way the library's own `tests/test_errors.py` does.)
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run the full suite `pytest -v` → PASS.
- [ ] **Step 5:** Smoke test against live EA: `DB_PATH=/tmp/me.db .venv/bin/uvicorn app.main:app --port 8000`, wait about 10 s, then `curl -s localhost:8000/api/overview | head -c 400` shows "Mind Eaters FC" and `curl -s localhost:8000/api/status` shows `lastError: null`.
- [ ] **Step 6:** `docker build -t mind-eaters-api api/` succeeds.
- [ ] **Step 7:** Commit `feat(api): collector, routes and Dockerfile`.

---

### Task 7: Web scaffold, theme and layout

**Files:**
- Create: `web/` (Vite React TS), `web/src/{main.tsx,App.tsx,api.ts,types.ts,theme.css,format.ts}`, `web/src/components/{Header,Tabs,StateMessage}.tsx`, `web/src/__tests__/format.test.ts`, `web/src/__tests__/App.test.tsx`

**Interfaces:**
- Consumes: the API Contract.
- Produces:
  - `types.ts` holds the exact contract types.
  - `api.ts` exports `getOverview(), getPlayers(), getPlayer(tag), getMatches(limit?), getMatch(id), getSeasons(), getStatus()`. Each returns a `Promise` of its type. It throws `NoDataYet` on 503 and `NotFound` on 404, against the relative base `/api`.
  - `format.ts` exports `fmtDate(iso): string` (e.g. `"Thu 29 Oct"`, in `America/Sao_Paulo`), `fmtTime(iso): string` (`"22:36"`), and `ago(iso, now = new Date()): string` (`"5 min ago"`, `"3 h ago"`, `"2 days ago"`).
  - `<StateMessage kind="loading"|"no-data"|"error" />`. The no-data copy is exactly "Collecting the first data from EA… check back in a few minutes."
  - Routes: `/` Overview, `/players`, `/players/:gamertag`, `/matches`, `/seasons`. The layout is `Header` (crest, name, division, skill rating, "updated X ago" from status) above `Tabs` (green underline on the active tab, as in the mockup).
  - `theme.css` holds the `:root` tokens and the shared classes from `look-v1.html` (`.tile`, `.card`, `.pc`, `.form`, `.W/.D/.L`, `.dnf`, background gradients, `rise` animation). Fonts are loaded via `<link>` in `index.html`.
  - `vite.config.ts` proxies `/api` to `http://localhost:8000` in dev, and sets up Vitest with jsdom.

- [ ] **Step 1:** `npm create vite@latest web -- --template react-ts`, add `react-router-dom@6`, and dev deps `vitest jsdom @testing-library/react @testing-library/jest-dom`. Add the `"test": "vitest run"` script.
- [ ] **Step 2: Write the failing tests:**

```ts
test("ago", () => {
  const now = new Date("2026-10-30T12:00:00-03:00");
  expect(ago("2026-10-30T11:55:00-03:00", now)).toBe("5 min ago");
  expect(ago("2026-10-30T09:00:00-03:00", now)).toBe("3 h ago");
});
test("fmtDate uses São Paulo time", () => {
  expect(fmtDate("2026-10-30T01:30:00Z")).toBe("Thu 29 Oct");   // 22:30 on the 29th in -03:00
});
test("tabs render and route", async () => { /* mock fetch; render App at /players; "Players" tab has aria-current="page" */ });
```

- [ ] **Step 3:** `npm test` → FAIL. **Step 4:** Implement. **Step 5:** `npm test` → PASS, `npm run build` → OK.
- [ ] **Step 6:** Commit `feat(web): scaffold, theme and layout`.

---

### Task 8: Overview page

**Files:**
- Create: `web/src/components/{StatStrip,FormStrip,MatchRow,PlayerCard,Leaders,MvpBars}.tsx`, `web/src/pages/Overview.tsx`, `web/src/__tests__/Overview.test.tsx`

**Interfaces:**
- Consumes: `getOverview`, `Match`, `Player`, `StateMessage`.
- Produces (reused by later pages): `<FormStrip matches={Match[]} />`, `<MatchRow match={Match} onClick? />` (shows opponent, score, result badge, a `DNF` tag when `dnf`, "⭐ {motm.displayName}" or "no MOTM"), `<PlayerCard player={Player} />` (links to `/players/{gamertag}`, shows overall, position abbreviation `MID/FWD/DEF/GK`, "⭐ {manOfTheMatch}", `displayName` with "gamertag · N games" underneath, G/A/RAT/PASS%, and a win-rate bar).
- The layout matches `look-v1.html`: stat strip, then the two-column grid (last matches | leaders + MVP bars), then player cards. All players are shown as cards (the mockup showed 4). It collapses to one column under 900 px.

- [ ] **Step 1: Write the failing tests** with a fixture overview object built from spec values:

```ts
test("shows season record and points", ...)        // "19", "7", "12", "28 pts"
test("shows MOTM or 'no MOTM'", ...)               // one match with motm null -> "no MOTM"
test("shows DNF tag", ...)
test("player card shows displayName and gamertag", ...) // "Reginaldo", "netozeraaa · 108 games"
test("503 shows collecting message", ...)          // getOverview rejects NoDataYet -> exact copy
```

- [ ] **Step 2:** FAIL → **Step 3:** implement → **Step 4:** PASS.
- [ ] **Step 5:** Visual check: run the API (Task 6 step 5) and `npm run dev`, then open `/` at desktop and at 390 px wide. It should look like `look-v1.html` with live data and no horizontal scroll.
- [ ] **Step 6:** Commit `feat(web): overview page`.

---

### Task 9: Players grid and player page

**Files:**
- Create: `web/src/pages/{Players,PlayerPage}.tsx`, `web/src/components/Sparkline.tsx`, `web/src/__tests__/PlayerPage.test.tsx`

**Interfaces:**
- Consumes: `getPlayers`, `getPlayer`, `PlayerCard`, `NotFound`.
- Produces: `<Sparkline values={number[]} />` (an inline SVG polyline in a purple→green gradient, no library).
- The Players page is a grid of `PlayerCard`, sorted by goals.
- The PlayerPage has a hero (big card), an "At the club" panel with every Player field labeled in plain words, and a "Since tracking started" panel (`tracked` totals). It also shows a rating sparkline over `history` and a recent-matches list (date, rating, G, A, ⭐). A 404 shows "Player not found" with a link back to Players.

- [ ] **Step 1: Write the failing tests:** renders every stat label (e.g. "Pass accuracy 78%", "Tackle success 35%", "Red cards 0"); shows "Since tracking started" with `tracked.games`; NotFound → "Player not found".
- [ ] **Step 2:** FAIL → **Step 3:** implement → **Step 4:** PASS.
- [ ] **Step 5:** Commit `feat(web): players grid and player page`.

---

### Task 10: Matches page

**Files:**
- Create: `web/src/pages/Matches.tsx`, `web/src/__tests__/Matches.test.tsx`

**Interfaces:**
- Consumes: `getMatches`, `getMatch`, `MatchRow`, `fmtDate`, `fmtTime`.
- Each session renders a header `"{fmtDate(start)} · {wins}W {draws}D {losses}L"` above its `MatchRow`s. Clicking a row expands it in place, loads `getMatch`, and shows a per-player table (name, position, rating, G, A, shots, passes made/attempts, tackles made/attempts, saves, minutes = `round(secondsPlayed/60)`, ⭐). The MOTM row is highlighted green.

- [ ] **Step 1: Write the failing tests:** the session header text is `"Thu 29 Oct · 7W 2D 1L"` for a fixture; clicking a row shows the player table with `"76"` minutes for `secondsPlayed: 4549`.
- [ ] **Step 2:** FAIL → **Step 3:** implement → **Step 4:** PASS.
- [ ] **Step 5:** Commit `feat(web): matches page grouped by session`.

---

### Task 11: Seasons page

**Files:**
- Create: `web/src/pages/Seasons.tsx`, `web/src/__tests__/Seasons.test.tsx`

**Interfaces:**
- Consumes: `getSeasons`.
- Each EA season is a block whose header reads "EA season · {fmtDate(startedAt)} – {endedAt ? fmtDate : 'now'}" and shows the totals (W/D/L, points, goals, promotions/relegations). When `partial`, it adds the badge "Since tracking started", and when `promotionsBeforeTracking > 0`, the line "{n} promotions before tracking". Inside the block are campaign cards: "Div {division}", an outcome pill (`promoted` green ↑, `relegated` red ↓, `stayed` grey, `in_progress` purple "In progress"), "{wins+draws+losses} games · {W}W {D}D {L}L", goals, top scorer and top MVP. When a campaign is `partial`, its card shows "since tracking started".

- [ ] **Step 1: Write the failing tests:** a partial season shows "Since tracking started" and "2 promotions before tracking"; the outcome pills render for all four outcomes.
- [ ] **Step 2:** FAIL → **Step 3:** implement → **Step 4:** PASS.
- [ ] **Step 5:** Commit `feat(web): seasons page with division campaigns`.

---

### Task 12: Web image and CI pipeline

**Files:**
- Create: `web/Dockerfile`, `web/nginx.conf`, `.github/workflows/deploy.yml`

**Interfaces:**
- Produces: images `ghcr.io/mariomendonca/mind-eaters-api:<sha>` and `ghcr.io/mariomendonca/mind-eaters-web:<sha>`, plus a dispatch of `deploy-mind-eaters.yml` in `mariomendonca/personal-vps-infra` with inputs `api_image` and `web_image`.
- `web/Dockerfile`: a `node:22-alpine` build stage, then `nginx:1.27-alpine` serving `dist/`. `nginx.conf` does an SPA fallback (`try_files $uri /index.html`), sets long cache headers for `/assets/*`, and adds `HEALTHCHECK` with `wget -qO- http://127.0.0.1/`.
- `deploy.yml` runs on push to `main` with these jobs: `test-api` (pytest), `test-web` (`npm ci && npm test && npm run build`), and `images` (needs both; builds and pushes both images using `GITHUB_TOKEN` with `packages: write`, then runs `gh workflow run deploy-mind-eaters.yml -R mariomendonca/personal-vps-infra -f api_image=… -f web_image=…` with `GH_TOKEN: ${{ secrets.INFRA_DISPATCH_TOKEN }}`).

- [ ] **Step 1:** Write the files. Check that `docker build -t mind-eaters-web web/` works, then run `docker run --rm -p 8080:80 mind-eaters-web`: `curl -s localhost:8080/players` returns the index HTML (SPA fallback).
- [ ] **Step 2:** Commit `ci: build images and dispatch infra deploy`.

---

### Task 13: Infra stack, Caddy and deploy workflow (repo `personal-vps-infra`)

**Files (in `/Users/mariomendonca/Desktop/projects/vps/personal-vps-infra`):**
- Create: `mind-eaters/docker-compose.prod.yml`, `mind-eaters/.env.production.example`, `.github/workflows/deploy-mind-eaters.yml`
- Modify: `proxy/Caddyfile` (append a block), `README.md` (architecture tree, networks list, first deploy, update deploy, CI/CD list)

**Interfaces:**
- Compose: project name `mind-eaters`, with services `api` (`container_name: mind-eaters-api`, `image: ${API_IMAGE}`, env `CLUB_ID`, `TZ=America/Sao_Paulo`, `DB_PATH=/data/mind-eaters.db`, volume `mind_eaters_data:/data`, `mem_limit: 256m`, `cpus: 0.5`) and `web` (`container_name: mind-eaters-web`, `image: ${WEB_IMAGE}`, `mem_limit: 64m`). Both have `restart: unless-stopped`, healthchecks, and the external network `proxy`.
- `.env.production.example`: `API_IMAGE=ghcr.io/mariomendonca/mind-eaters-api:main`, `WEB_IMAGE=ghcr.io/mariomendonca/mind-eaters-web:main`, `CLUB_ID=1232878`.
- `deploy-mind-eaters.yml`: copy `deploy-loyalty-card.yml`'s structure (secret check, `appleboy/ssh-action`, `git pull --ff-only`, network ensure, GHCR login) with inputs `api_image`/`web_image`. It writes the given images into `mind-eaters/.env.production` (keeping current values when blank), runs `pull` + `up -d`, and fails if `mind-eaters-api` is not `healthy` within 60 s. Concurrency group `mind-eaters`.
- Caddy block:

```
# Mind Eaters FC dashboard (Pro Clubs stats). Public, kept out of search engines.
mindeatersfc.mariomendonca.dev {
	encode gzip zstd
	header X-Robots-Tag "noindex, nofollow"

	handle /api/* {
		reverse_proxy mind-eaters-api:8000
	}

	handle {
		reverse_proxy mind-eaters-web:80
	}
}
```

- [ ] **Step 1:** Write the files. Validate with `docker compose -f mind-eaters/docker-compose.prod.yml --env-file mind-eaters/.env.production.example config` (exits 0) and `docker run --rm -v "$PWD/proxy:/etc/caddy" caddy:2-alpine caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile` (env-var placeholders may warn; there should be no parse errors).
- [ ] **Step 2:** Commit in the infra repo: `feat: add mind-eaters stack, proxy route and deploy workflow`.

---

### Task 14: First deploy (with the owner)

These steps need the owner's accounts and DNS. The executor prepares the commands and the owner runs or approves them.

- [ ] **Step 1:** Owner adds the DNS A record `mindeatersfc.mariomendonca.dev` pointing to the VPS IP.
- [ ] **Step 2:** In the existing GitHub repo `mariomendonca/mind-eaters-fc-pro-clubs`, owner adds the secret `INFRA_DISPATCH_TOKEN` (the same PAT style as loyalty-card) and pushes `main`. The infra repo changes get pushed too.
- [ ] **Step 3:** On the VPS: `cd /opt/apps/infra && git pull && cp mind-eaters/.env.production.example mind-eaters/.env.production`, then run `deploy-proxy.yml`.
- [ ] **Step 4:** The `deploy.yml` run is green and `deploy-mind-eaters.yml` is green.
- [ ] **Step 5:** Verify: `curl -sI https://mindeatersfc.mariomendonca.dev | grep -i x-robots` shows noindex. `curl -s https://mindeatersfc.mariomendonca.dev/api/status` shows `lastSuccessAt` set within 15 min. The page loads on a phone.
- [ ] **Step 6:** Check that no data was lost after a redeploy: re-run `deploy-mind-eaters.yml`, and the `/api/matches` count is unchanged.
