import type { Match, Result } from "../types";

const LETTER: Record<Result, "W" | "D" | "L"> = { win: "W", draw: "D", loss: "L" };

export function ResultBadge({ result }: { result: Result }) {
  const l = LETTER[result];
  return (
    <span className={`badge ${l}`} aria-label={result}>
      {l}
    </span>
  );
}

export function FormStrip({ matches }: { matches: Match[] }) {
  return (
    <div className="form" aria-label="Recent form, newest first">
      {matches.map((m) => (
        <ResultBadge key={m.matchId} result={m.result} />
      ))}
    </div>
  );
}
