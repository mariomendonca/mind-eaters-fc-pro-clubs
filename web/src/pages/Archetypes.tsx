import { Link } from "react-router-dom";
import { getArchetypes } from "../api";
import { Loaded } from "../components/Loaded";
import { StateMessage } from "../components/StateMessage";
import { fmtDate, pct, perGame } from "../format";
import type { ArchetypeRecord } from "../types";
import { useLoad } from "../useLoad";

function RecordBar({ a }: { a: ArchetypeRecord }) {
  const share = (n: number) => (a.games ? (n / a.games) * 100 : 0);
  return (
    <div className="tod-bar" aria-hidden="true">
      {a.wins > 0 && <i className="W" style={{ width: `${share(a.wins)}%` }} />}
      {a.draws > 0 && <i className="D" style={{ width: `${share(a.draws)}%` }} />}
      {a.losses > 0 && <i className="L" style={{ width: `${share(a.losses)}%` }} />}
    </div>
  );
}

function ArchetypeCard({ a, index }: { a: ArchetypeRecord; index: number }) {
  return (
    <section className="card archetype" data-testid={`archetype-${a.id}`} style={{ animationDelay: `${Math.min(index, 6) * 0.05}s` }}>
      <div className="tod-head">
        <h3 className="archetype-name">{a.name}</h3>
        <span className="tod-rate">{a.winRate}%</span>
      </div>
      <RecordBar a={a} />
      <div className="bl">
        <span data-testid={`archetype-record-${a.id}`}>
          Team: {a.wins}W {a.draws}D {a.losses}L · {a.games} {a.games === 1 ? "game" : "games"}
        </span>
        <span>
          {a.goals} G · {a.assists} A · rating {a.avgRating == null ? "–" : a.avgRating.toFixed(1)}
        </span>
      </div>
      <div className="table-wrap">
        <table className="stats">
          <thead>
            <tr>
              <th>Player</th>
              <th className="n">Games</th>
              <th className="n">W-D-L</th>
              <th className="n">Win %</th>
              <th className="n">G</th>
              <th className="n">A</th>
              <th className="n">G/game</th>
              <th className="n">A/game</th>
              <th className="n">Rating</th>
              <th className="n">MOTM</th>
              <th className="n">Last played</th>
            </tr>
          </thead>
          <tbody>
            {a.players.map((p) => (
              <tr key={p.gamertag}>
                <td>
                  <Link to={`/players/${encodeURIComponent(p.gamertag)}`} className="player-link">
                    {p.displayName}
                  </Link>
                </td>
                <td className="n">{p.games}</td>
                <td className="n">
                  {p.wins}-{p.draws}-{p.losses}
                </td>
                <td className="n">{pct((p.wins / p.games) * 100)}</td>
                <td className="n">{p.goals}</td>
                <td className="n">{p.assists}</td>
                <td className="n">{perGame(p.goals, p.games)}</td>
                <td className="n">{perGame(p.assists, p.games)}</td>
                <td className="n">{p.avgRating == null ? "–" : p.avgRating.toFixed(1)}</td>
                <td className="n">{p.motm}</td>
                <td className="n muted">{fmtDate(p.lastPlayed)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function Archetypes() {
  const state = useLoad(getArchetypes);
  return (
    <Loaded state={state}>
      {({ archetypes, unused }) =>
        archetypes.length === 0 ? (
          <StateMessage kind="no-data">No archetypes in the saved matches yet.</StateMessage>
        ) : (
          <>
            <div className="tod-legend muted">
              <span><i className="W" /> Win</span>
              <span><i className="D" /> Draw</span>
              <span><i className="L" /> Loss</span>
            </div>
            {archetypes.map((a, i) => (
              <ArchetypeCard key={a.id} a={a} index={i} />
            ))}
            {unused.length > 0 && (
              <p className="muted archetypes-unused" data-testid="unused">
                Not played yet: {unused.join(", ")}
              </p>
            )}
            <p className="note">
              Most-played archetypes first. The team record counts a match once even if two of us used the same archetype; each player's row is
              only their own games with it. Archetype names come from community research on EA's data (EA doesn't publish them).
            </p>
          </>
        )
      }
    </Loaded>
  );
}
