import { Link, useParams } from "react-router-dom";
import { getPlayer } from "../api";
import { Loaded } from "../components/Loaded";
import { PlayerCard } from "../components/PlayerCard";
import { Sparkline } from "../components/Sparkline";
import { StateMessage } from "../components/StateMessage";
import { fmtDate, fmtTime, pct } from "../format";
import type { Player } from "../types";
import { useLoad } from "../useLoad";

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="stat">
      <span>{label}</span>
      <b>{value}</b>
    </div>
  );
}

function clubStats(p: Player): [string, React.ReactNode][] {
  return [
    ["Games", p.gamesPlayed],
    ["Goals", p.goals],
    ["Assists", p.assists],
    ["Average rating", p.averageRating.toFixed(1)],
    ["Man of the Match", p.manOfTheMatch],
    ["Win rate", pct(p.winRate)],
    ["Pass accuracy", pct(p.passSuccessRate)],
    ["Passes made", p.passesMade],
    ["Shot accuracy", pct(p.shotSuccessRate)],
    ["Tackles made", p.tacklesMade],
    ["Tackle success", pct(p.tackleSuccessRate)],
    ["Clean sheets", (p.cleanSheetsDef ?? 0) + (p.cleanSheetsGK ?? 0)],
    ["Red cards", p.redCards],
  ];
}

export function PlayerPage() {
  const { gamertag = "" } = useParams();
  const state = useLoad(() => getPlayer(gamertag), [gamertag]);
  const back = (
    <Link to="/players" className="back">
      ← Back to players
    </Link>
  );
  return (
    <>
      {back}
      <Loaded state={state} notFound={<StateMessage kind="not-found">Player not found</StateMessage>}>
        {({ player, history, tracked }) => (
          <div className="player-layout">
            <div className="player-hero">
              <PlayerCard player={player} />
            </div>
            <div>
              <div className="card" data-testid="at-club">
                <h3>
                  At the club <small>EA totals</small>
                </h3>
                <div className="stat-grid">
                  {clubStats(player).map(([label, value]) => (
                    <Stat key={label} label={label} value={value} />
                  ))}
                </div>
              </div>
              <div className="card" data-testid="tracked">
                <h3>
                  Since tracking started <small>from saved matches</small>
                </h3>
                <div className="stat-grid">
                  <Stat label="Games" value={tracked.games} />
                  <Stat label="Goals" value={tracked.goals} />
                  <Stat label="Assists" value={tracked.assists} />
                  <Stat label="MOTM" value={tracked.motm} />
                  <Stat label="Avg rating" value={tracked.avgRating} />
                </div>
                <div style={{ marginTop: 16 }}>
                  <Sparkline values={history.map((h) => h.rating)} />
                </div>
              </div>
              <div className="card" data-testid="history">
                <h3>
                  Recent matches <small>newest first</small>
                </h3>
                {history.length === 0 ? (
                  <p className="muted">No saved matches for this player yet.</p>
                ) : (
                  <div className="table-wrap">
                    <table className="stats">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th className="n">Rating</th>
                          <th className="n">G</th>
                          <th className="n">A</th>
                          <th className="n">MOTM</th>
                        </tr>
                      </thead>
                      <tbody>
                        {[...history].reverse().slice(0, 20).map((h) => (
                          <tr key={h.matchId} className={h.motm ? "is-motm" : undefined}>
                            <td>
                              {fmtDate(h.timestamp)} · {fmtTime(h.timestamp)}
                            </td>
                            <td className="n">{h.rating.toFixed(1)}</td>
                            <td className="n">{h.goals}</td>
                            <td className="n">{h.assists}</td>
                            <td className="n">{h.motm ? "⭐" : ""}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </Loaded>
    </>
  );
}
