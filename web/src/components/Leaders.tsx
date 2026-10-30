import type { Leader, Overview } from "../types";

function Lead({ label, leader, digits = 0 }: { label: string; leader: Leader; digits?: number }) {
  return (
    <div className="lead">
      <div className="label">{label}</div>
      <div className="v">{leader ? leader.value.toFixed(digits) : "–"}</div>
      <div className="who">{leader?.displayName ?? "—"}</div>
    </div>
  );
}

export function Leaders({ leaders }: { leaders: Overview["leaders"] }) {
  return (
    <div className="leaders">
      <Lead label="Goals" leader={leaders.goals} />
      <Lead label="Assists" leader={leaders.assists} />
      <Lead label="Avg rating" leader={leaders.rating} digits={1} />
    </div>
  );
}
