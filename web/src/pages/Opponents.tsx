import { useState } from "react";
import { getOpponents } from "../api";
import { Loaded } from "../components/Loaded";
import { StateMessage } from "../components/StateMessage";
import { fmtDate } from "../format";
import type { Opponent } from "../types";
import { useLoad } from "../useLoad";
import { ExpandableMatch } from "./Matches";

/** Lower-case and strip accents so "sao" finds "São". */
const fold = (s: string) => s.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();

function OpponentRow({ o }: { o: Opponent }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="opponent" data-testid="opponent">
      <button type="button" className="opponent-row" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        <span className="opp">
          {o.crestUrl ? <img src={o.crestUrl} alt="" loading="lazy" /> : <i className="crest-blank" aria-hidden="true" />}
          <span>{o.name}</span>
          {o.games > 1 && <span className="pill games">{o.games}×</span>}
        </span>
        <span className="opp-record">
          <b className="w">{o.wins}W</b> <b className="d">{o.draws}D</b> <b className="l">{o.losses}L</b>
        </span>
        <span className="sc">
          {o.goals}–{o.goalsAgainst}
        </span>
        <span className="muted opp-last">{fmtDate(o.lastPlayed)}</span>
      </button>
      {open && (
        <div className="opponent-matches">
          {o.matches.map((m) => (
            <ExpandableMatch key={m.matchId} match={m} />
          ))}
        </div>
      )}
    </div>
  );
}

function OpponentList({ opponents }: { opponents: Opponent[] }) {
  const [query, setQuery] = useState("");
  const [rematchesOnly, setRematchesOnly] = useState(false);
  const rematches = opponents.filter((o) => o.games > 1).length;
  const q = fold(query.trim());
  const shown = opponents.filter((o) => (!rematchesOnly || o.games > 1) && (!q || fold(o.name).includes(q)));

  return (
    <section className="card">
      <h3>
        <span>Opponents</span>
        <small>
          {opponents.length} {opponents.length === 1 ? "club" : "clubs"} faced
        </small>
      </h3>
      <div className="opp-filters">
        <input
          type="search"
          className="search"
          placeholder="Search team…"
          aria-label="Search team"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="button" className={`chip${rematchesOnly ? " on" : ""}`} aria-pressed={rematchesOnly} onClick={() => setRematchesOnly((v) => !v)}>
          Played 2+ times ({rematches})
        </button>
      </div>
      {shown.length ? (
        shown.map((o) => <OpponentRow key={o.opponentId ?? o.name} o={o} />)
      ) : (
        <p className="muted opp-empty">No teams match.</p>
      )}
    </section>
  );
}

export function Opponents() {
  const state = useLoad(getOpponents);
  return (
    <Loaded state={state}>
      {(opponents) =>
        opponents.length === 0 ? (
          <StateMessage kind="no-data">No matches tracked yet.</StateMessage>
        ) : (
          <>
            <OpponentList opponents={opponents} />
            <p className="note">Click a team to see every match against them. Most-played teams first. History starts from 30 Oct 2026.</p>
          </>
        )
      }
    </Loaded>
  );
}
