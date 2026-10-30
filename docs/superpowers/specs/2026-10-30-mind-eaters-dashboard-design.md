# Mind Eaters FC Dashboard — Design

**Date:** 2026-10-30
**Status:** Draft, awaiting approval
**Visual reference:** `docs/design/look-v1.html` (approved look)

## 1. Intent

Mind Eaters FC is an EA Sports FC 27 Pro Clubs team (club ID `1232878`, platform `common-gen5`). The squad wants a dashboard they open, mostly after a play session, to see how the club and each player are doing: player stats, the MVP of each game, club stats, and how each season and division went.

EA has no official API and its endpoints keep almost no history (last 10 matches, current season totals, all-time totals). So the dashboard's second job is to **build the club's history itself, from today on**, by saving what EA returns regularly. There are no past seasons to import.

**Success:** after a session, any squad member opens `https://mindeatersfc.mariomendonca.dev` on a phone or desktop and immediately sees last night's results with MVPs, current form, and player stats. Over months, the Matches and Seasons tabs grow into a real club history.

## 2. Goals, non-goals, anti-goals

**Goals**
- Show every stat EA provides for the club and each player, in the approved purple and green look.
- Save every league match (and per-player match stats) and club snapshots so history accumulates beyond EA's 10-match window.
- Track seasons (division, W/D/L, points, promotion/relegation, top scorer, MVP) starting now.
- Deploy on the owner's VPS using the existing `personal-vps-infra` pattern.

**Non-goals (for now)**
- Multiple clubs, club search, or comparing against other clubs.
- Logins, user accounts, editing data by hand.
- Importing past seasons (the owner confirmed there are none).
- Friendlies and playoffs as first-class features. EA currently returns `[]` for both for this club; save them if they appear, but no dedicated UI.

**Anti-goals (failure even if it "works")**
- Looking like a generic admin template. The approved look is a core requirement.
- Losing matches: if a session has more than 10 games and we only collect once afterwards, the early games are gone forever. Collection frequency must make this unlikely (see §5.3).
- Hammering EA. Keep requests modest (≤ ~10 per collection run, 1s apart) so the VPS IP doesn't get blocked.

## 3. Verified facts about the data source

Tested live on 2026-10-30 with the `fc-clubs-api` Python library (https://github.com/1erkandogan/fc27-clubs-api, MIT, PyPI `fc-clubs-api`). All of these returned real data:

| Library method | What we get (this club) |
|---|---|
| `get_club_details(cid)` | name, crest URL, stadium ("Estádio de ní"), regionId, teamId |
| `get_club_overall_stats(cid)` | all-time: 123 GP, 63W 15D 45L, 360 GF / 285 GA, skillRating 1782, winStreak, unbeatenStreak, promotions 6, relegations 0, bestDivision 2, reputationTier |
| `search_club_by_name(name, scope="current_season")` | **current season**: 38 GP, 19W 7D 12L, 120 GF / 108 GA, points 28, currentDivision 4, promotions 2 (this season), cleanSheets |
| `search_club_by_name(name, scope="all_time")` | all-time leaderboard row incl. currentDivision, bestDivision, points |
| `get_member_stats(cid)` | 8 members: `name` (gamertag), `playerName` (in-game name), position, overall, gamesPlayed, winRate, goals, assists, averageRating, manOfTheMatch, shotSuccessRate, passesMade, passSuccessRate, tacklesMade, tackleSuccessRate, cleanSheetsDef, cleanSheetsGK, redCards |
| `get_member_career_stats(cid)` | per member: GP, goals, assists, averageRating, MOTM |
| `get_club_matches(cid, "leagueMatch", 10)` | last 10 league matches: matchId, timestamp, opponent name/id/crest, goals, goalsAgainst, result (win/draw/loss), dnf |
| `get_match_players(cid, "leagueMatch", 10)` | per player per match: playerId, name, position, rating, goals, assists, shots, passesMade/Attempts, tacklesMade/Attempts, saves, cleanSheet, manOfTheMatch, redCards, secondsPlayed. Supports `both_teams=True`, `include_events=True` (80+ decoded event stats) |

**Quirks the builder must handle**
1. **EA caps matches at 10, no paging.** History exists only if we save it.
2. **Member stats are totals at the club, not this season.** Reginaldo shows 108 GP while the club has played 38 this season (and 123 all-time). "This season" per-player numbers must be computed from our saved match-player rows.
3. **Player identity:** `name` is the gamertag (stable key; one member's is a hex hash `6d9dd2e578c1d7a9`), `playerName` is the in-game name ("J. Show"). Display `playerName` large with the gamertag small. Use gamertag (and `playerId` in match rows) as keys.
4. **MOTM can be absent** for a match (2 of the last 10 had nobody flagged). Show "no MOTM" — don't fall back silently to the best rating. The highest rating per match may be shown separately.
5. **DNF matches** exist (2 of the last 10). Show a DNF tag; still count them as EA does.
6. **EA blocks non-browser clients** (Akamai). The library sends browser headers; plain curl is blocked. Requests from a data-center IP (the VPS) are **untested** — see §7 risk.
7. **Timestamps:** use timezone `America/Sao_Paulo` for display and for grouping matches into sessions.
8. Unofficial API — endpoints can change. Fail soft: the dashboard keeps serving saved data and shows "last updated X ago" when collection fails.

## 4. What the dashboard shows

Four tabs, in the approved look (dark, purple `#8b3dff` + green `#39ff88`, Big Shoulders Display / Familjen Grotesk / Martian Mono). The overview layout is the approved mockup; other tabs follow the same visual language.

### 4.1 Overview (approved mockup)
- Header: crest, club name, current division and best division, promotions/relegations, stadium, skill rating.
- Stat strip: this season (W/D/L, points, games, W/D/L bar), all-time games, all-time win rate, goals for/against/diff, current streak.
- Last 10 matches: form strip + list with opponent, score, MOTM, DNF tag.
- Club leaders (all-time at the club): goals, assists, average rating.
- MVP count over recent matches (from saved history; "last 10" until more history exists).
- Player cards: overall, position, MOTM count, goals, assists, rating, pass %, win rate. Clicking opens the player page.
- "Last updated" indicator.

### 4.2 Players
- Grid of all player cards (same card component as overview).
- **Player page:** every EA member stat (§3), career stats, plus from our history: rating trend across saved matches, MOTM count, goals/assists per session, this-season totals computed from saved matches (clearly labeled "since we started tracking" until a full season is saved).

### 4.3 Matches
- Every saved match, newest first, **grouped by session** (a session = matches with gaps under ~2 hours between them; header like "Thu 29 Oct · 7W 2D 1L").
- Each match: opponent + crest, score, result, DNF, MOTM, highest-rated player. Expanding shows the per-player table (rating, goals, assists, shots, passes, tackles, saves, minutes).

### 4.4 Seasons
Two levels (owner confirmed): **division campaigns are the main view, grouped under each EA season.**
- **EA season:** the block of games until EA resets the current-season leaderboard (this EA season had 38 games and 2 promotions on 2026-10-30). Header shows EA-season totals: W/D/L, points, goals, promotions/relegations.
- **Division campaign** (inside an EA season): one card per stint in a division, e.g. "Div 5 · promoted · 10 games · 8W 1D 1L". Shows division, W/D/L, goals, outcome (promoted / relegated / stayed / in progress), top scorer and top MVP from saved matches in that stint.
- The current campaign is shown as "in progress". The first EA season and the first campaign are partial (tracking began 2026-10-30) and must be labeled "since tracking started". Earlier campaigns this EA season are unknown and are not invented. At most, the EA-season header can say "2 promotions before tracking".

## 5. Architecture

### 5.1 Components
- **API:** Python, using `fc-clubs-api` (pin the version). Owner chose Python. Exposes JSON under `/api/*` for the frontend and runs the background collector.
- **Web:** React (Vite) SPA, built to static files and served by nginx.
- **Storage:** SQLite file on a Docker named volume.

### 5.2 Data stored (shape, not exact schema)
- `matches` — one row per matchId: timestamp, matchType, opponent id/name/crest, goals, goalsAgainst, result, dnf, season id. Also keep EA's raw JSON per match so new fields can be backfilled later.
- `match_players` — one row per (matchId, playerId): all per-player fields incl. MOTM, rating, seconds played. Ours only (both_teams not needed for v1); store `include_events` data if cheap.
- `club_snapshots` — each collection run: overall stats + current-season row (GP, W/D/L, points, division, promotions/relegations this season, skill rating).
- `member_snapshots` — each collection run (or only when changed): member stats per gamertag.
- `seasons` — derived: season number (ours), start/end, division, final record, outcome.

Inserts must be idempotent (matchId is the dedupe key) since every run re-fetches the same 10 matches.

### 5.3 Collection
- Background job inside the API process (or a sidecar loop in the same image). **Every 15 minutes** pull: current-season search, overall stats, member stats, league matches, match players (~5–6 EA calls, 1s apart). Club details/crest less often (daily).
- Rationale: a session of more than 10 matches within one interval is very unlikely, so no matches are lost.
- On failure: log, keep last good data, expose `lastSuccessfulCollection` and `lastError` via `/api/health` / `/api/status`.
- **EA season boundary:** a new EA season started when the current-season `gamesPlayed` goes down compared with the previous snapshot (or the promotion/relegation counters reset). Close the previous EA season using its last snapshot before the reset.
- **Division campaign boundary:** a new campaign starts when `currentDivision` changes between snapshots (promotion or relegation; compare with the season's promotion/relegation counters to label the outcome), or when a new EA season starts. Per-campaign W/D/L comes from saved matches. Cross-check it against the difference between the snapshots at the campaign's start and end, and log any mismatch.
- Matches are assigned to the EA season and campaign that were active at their timestamp. A division change detected mid-interval is attributed at the snapshot time. Matches between the last snapshot before the change and the one after it can be ambiguous, so attribute them by timestamp against the snapshot where the division changed (builder may refine).

### 5.4 Deployment (follows `personal-vps-infra`)
- App repo: GitHub `mariomendonca/mind-eaters-fc-pro-clubs` (local folder `mind-eaters-fc/`) builds two images on push to `main` — `ghcr.io/mariomendonca/mind-eaters-api`, `ghcr.io/mariomendonca/mind-eaters-web` — SHA-tagged, then dispatches the infra workflow using `INFRA_DISPATCH_TOKEN` (same as loyalty-card).
- Infra repo gets:
  - `mind-eaters/docker-compose.prod.yml` + `.env.production.example`: containers `mind-eaters-api` and `mind-eaters-web` on the external `proxy` network. No private network is needed because SQLite runs inside the API process. Healthchecks on both, `mem_limit`/`cpus` set, `restart: unless-stopped`, SQLite on named volume `mind_eaters_data`.
  - `.github/workflows/deploy-mind-eaters.yml`, modeled on `deploy-loyalty-card.yml` (inputs `api_image`, `web_image`; fails if API isn't healthy).
  - `proxy/Caddyfile` block for `mindeatersfc.mariomendonca.dev`: `/api/*` → `mind-eaters-api:<port>`, everything else → `mind-eaters-web:80`, `encode gzip zstd`, `X-Robots-Tag "noindex, nofollow"`. Public, no basic_auth.
  - README section for the new stack.
- DNS: A record `mindeatersfc.mariomendonca.dev` → VPS (owner does this).
- Backups: SQLite copy to R2 is a nice-to-have, reusing `scripts/lib/r2.sh`; not required for v1 but the volume must not be lost on redeploy.

## 6. Decisions

**Made by the owner**
- Python backend; React frontend.
- Approved visual look (`look-v1.html`), tabbed structure (Overview · Players · Matches · Seasons), club colors purple + green.
- History starts now; no past-season import.
- Seasons tab: division campaigns as the main view, grouped under each EA season.
- Hosted on the personal VPS at `mindeatersfc.mariomendonca.dev`.

**Claude's calls (owner can override)**
- Public, no password, noindex.
- SQLite instead of Postgres.
- 15-minute collection interval.
- EA-season detection via the current-season games counter dropping; campaign detection via `currentDivision` changing.
- Session grouping with a ~2-hour gap.
- League matches only in the UI for v1.

## 7. Risks

1. ~~EA may block the VPS IP.~~ **Resolved 2026-10-30:** owner ran `fc-clubs-api` in a `python:3.12-slim` container on the VPS and EA returned the club. Keep request volume modest so it stays that way.
2. EA changes endpoints — pin library version, store raw JSON, fail soft.
3. Season detection is inferred, not given by EA — first real season rollover should be watched and the logic adjusted if needed.

## 8. Left to the builder
- Exact API routes and payload shapes, DB schema, migrations approach.
- Python web framework (FastAPI is a reasonable default), scheduler mechanism.
- React structure, routing, data fetching, charting library for the rating trend.
- Responsive details beyond the mockup (must work well on phones).
- Testing approach (use the library's fixtures style; mock EA in tests).
