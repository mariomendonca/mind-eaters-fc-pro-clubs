import type { Match } from "../types";
import { ResultBadge } from "./FormStrip";

export function MatchRow({ match, onClick, expanded }: { match: Match; onClick?: () => void; expanded?: boolean }) {
  const body = (
    <>
      <ResultBadge result={match.result} />
      <span className="opp">
        {match.opponentCrestUrl && <img src={match.opponentCrestUrl} alt="" loading="lazy" />}
        <span>{match.opponentName}</span>
        {match.dnf && <span className="dnf">DNF</span>}
      </span>
      <span className="sc">
        {match.goals}–{match.goalsAgainst}
      </span>
      {match.motm ? <span className="mvp">⭐ {match.motm.displayName}</span> : <span className="mvp none">no MOTM</span>}
    </>
  );
  if (onClick) {
    return (
      <button type="button" className="match" onClick={onClick} aria-expanded={expanded}>
        {body}
      </button>
    );
  }
  return <div className="match">{body}</div>;
}
