import type { Overview } from "../types";

export function StatStrip({ season, allTime }: Pick<Overview, "season" | "allTime">) {
  const winRate = allTime.gamesPlayed ? Math.round((allTime.wins / allTime.gamesPlayed) * 100) : 0;
  const diff = allTime.goals - allTime.goalsAgainst;
  return (
    <section className="strip">
      <div className="tile season" data-testid="season-tile">
        <div className="label">This season</div>
        <div className="v">
          {season.wins}
          <span className="g">W</span> {season.ties}
          <span style={{ color: "var(--draw)" }}>D</span> {season.losses}
          <span style={{ color: "var(--loss)" }}>L</span>
        </div>
        <div className="h">
          <b className="num">{season.points}</b> pts · {season.gamesPlayed} games
        </div>
        <div className="wdl" aria-hidden>
          <i style={{ flex: season.wins, background: "var(--green)" }} />
          <i style={{ flex: season.ties, background: "var(--draw)" }} />
          <i style={{ flex: season.losses, background: "var(--loss)" }} />
        </div>
      </div>
      <div className="tile">
        <div className="label">All-time games</div>
        <div className="v">{allTime.gamesPlayed}</div>
        <div className="h">
          {allTime.wins}W · {allTime.ties}D · {allTime.losses}L
        </div>
      </div>
      <div className="tile">
        <div className="label">Win rate</div>
        <div className="v g">{winRate}%</div>
        <div className="h">all-time</div>
      </div>
      <div className="tile">
        <div className="label">Goals</div>
        <div className="v">{allTime.goals}</div>
        <div className="h">
          {allTime.goalsAgainst} against · <span className={diff >= 0 ? "g" : undefined}>{diff >= 0 ? `+${diff}` : diff}</span>
        </div>
      </div>
      <div className="tile">
        <div className="label">Streak</div>
        <div className="v p">{allTime.unbeatenStreak}</div>
        <div className="h">
          unbeaten · {allTime.winStreak} {allTime.winStreak === 1 ? "win" : "wins"} in a row
        </div>
      </div>
    </section>
  );
}
