import type { Who } from "../types";

export function MvpBars({ counts }: { counts: (Who & { count: number })[] }) {
  if (!counts.length) return <p className="muted">No Man of the Match yet.</p>;
  const max = Math.max(...counts.map((c) => c.count));
  return (
    <div style={{ display: "grid", gap: 9 }}>
      {counts.map((c) => (
        <div key={c.gamertag}>
          <div className="bl">
            <span className="name">{c.displayName}</span>
            <span className="num">{c.count}</span>
          </div>
          <div className="bar">
            <i style={{ width: `${(c.count / max) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}
