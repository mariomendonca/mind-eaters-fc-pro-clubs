import { useState } from "react";
import { getMatch, getMatches } from "../api";
import { Loaded } from "../components/Loaded";
import { MatchRow } from "../components/MatchRow";
import { StateMessage } from "../components/StateMessage";
import { fmtDate, fmtTime, posLabel } from "../format";
import type { Match } from "../types";
import { useLoad } from "../useLoad";

function MatchPlayers({ id }: { id: string }) {
  const state = useLoad(() => getMatch(id), [id]);
  return (
    <div className="match-detail">
      <Loaded state={state}>
        {({ players }) => (
          <div className="table-wrap">
            <table className="stats">
              <thead>
                <tr>
                  <th>Player</th>
                  <th>Pos</th>
                  <th className="n">Rating</th>
                  <th className="n">G</th>
                  <th className="n">A</th>
                  <th className="n">Shots</th>
                  <th className="n">Passes</th>
                  <th className="n">Tackles</th>
                  <th className="n">Saves</th>
                  <th className="n">Min</th>
                </tr>
              </thead>
              <tbody>
                {players.map((p) => (
                  <tr key={p.gamertag} className={p.manOfTheMatch ? "is-motm" : undefined}>
                    <td>
                      {p.manOfTheMatch && "⭐ "}
                      {p.displayName}
                    </td>
                    <td>{posLabel(p.position)}</td>
                    <td className="n">{p.rating.toFixed(1)}</td>
                    <td className="n">{p.goals}</td>
                    <td className="n">{p.assists}</td>
                    <td className="n">{p.shots}</td>
                    <td className="n">
                      {p.passesMade}/{p.passAttempts}
                    </td>
                    <td className="n">
                      {p.tacklesMade}/{p.tackleAttempts}
                    </td>
                    <td className="n">{p.saves}</td>
                    <td className="n">{Math.round(p.secondsPlayed / 60)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Loaded>
    </div>
  );
}

function ExpandableMatch({ match }: { match: Match }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <MatchRow match={match} onClick={() => setOpen((o) => !o)} expanded={open} />
      {open && (
        <>
          <p className="muted match-time">
            {fmtDate(match.timestamp)} · {fmtTime(match.timestamp)}
            {match.best && ` · best rating ${match.best.displayName} ${match.best.rating.toFixed(1)}`}
          </p>
          <MatchPlayers id={match.matchId} />
        </>
      )}
    </>
  );
}

export function Matches() {
  const state = useLoad(() => getMatches(200));
  return (
    <Loaded state={state}>
      {({ sessions }) =>
        sessions.length === 0 ? (
          <StateMessage kind="no-data">No matches saved yet. They appear after the next session.</StateMessage>
        ) : (
          <>
            {sessions.map((s, i) => (
              <section key={s.start} className="card" style={{ animationDelay: `${i * 0.05}s` }}>
                <h3>
                  <span>{`${fmtDate(s.start)} · ${s.wins}W ${s.draws}D ${s.losses}L`}</span>
                  <small>
                    {s.matches.length} {s.matches.length === 1 ? "match" : "matches"} · from {fmtTime(s.start)}
                  </small>
                </h3>
                {s.matches.map((m) => (
                  <ExpandableMatch key={m.matchId} match={m} />
                ))}
              </section>
            ))}
            <p className="note">Click a match to see every player's stats. History starts from 30 Oct 2026.</p>
          </>
        )
      }
    </Loaded>
  );
}
