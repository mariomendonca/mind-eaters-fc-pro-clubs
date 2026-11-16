import { getTimeOfDay } from "../api";
import { Loaded } from "../components/Loaded";
import { StateMessage } from "../components/StateMessage";
import type { TimeSlot } from "../types";
import { useLoad } from "../useLoad";

const hh = (h: number) => `${String(h).padStart(2, "0")}:00`;

/** The slot with the highest win rate, or null when nothing was played or two slots tie. */
function bestSlot(slots: TimeSlot[]): TimeSlot | null {
  const played = slots.filter((s) => s.games > 0);
  if (!played.length) return null;
  const top = Math.max(...played.map((s) => s.winRate));
  const leaders = played.filter((s) => s.winRate === top);
  return leaders.length === 1 ? leaders[0] : null;
}

function SlotRow({ s, best }: { s: TimeSlot; best: boolean }) {
  const pct = (n: number) => (s.games ? (n / s.games) * 100 : 0);
  return (
    <div className={`tod-row${best ? " best" : ""}`} data-testid={`slot-${s.slot}`}>
      <div className="tod-head">
        <span className="name">
          {s.label} <span className="muted">{hh(s.startHour)}–{hh(s.endHour)}</span>
          {best && <span className="pill promoted">Best time</span>}
        </span>
        <span className="tod-rate">{s.games ? `${s.winRate}%` : "—"}</span>
      </div>
      <div className="tod-bar" aria-hidden="true">
        {s.wins > 0 && <i className="W" style={{ width: `${pct(s.wins)}%` }} />}
        {s.draws > 0 && <i className="D" style={{ width: `${pct(s.draws)}%` }} />}
        {s.losses > 0 && <i className="L" style={{ width: `${pct(s.losses)}%` }} />}
      </div>
      <div className="bl">
        <span data-testid={`record-${s.slot}`}>
          {s.wins}W {s.draws}D {s.losses}L
        </span>
        <span>
          {s.games} {s.games === 1 ? "game" : "games"}
        </span>
      </div>
    </div>
  );
}

export function Insights() {
  const state = useLoad(getTimeOfDay);
  return (
    <Loaded state={state}>
      {({ slots }) => {
        if (slots.every((s) => s.games === 0)) return <StateMessage kind="no-data">No matches tracked yet.</StateMessage>;
        const best = bestSlot(slots);
        return (
          <>
            <section className="card">
              <h3>
                <span>When do we win?</span>
                <small>{best ? `We win most in the ${best.label.toLowerCase()}` : "Win / draw / loss by time of day"}</small>
              </h3>
              <div className="tod-legend muted">
                <span><i className="W" /> Win</span>
                <span><i className="D" /> Draw</span>
                <span><i className="L" /> Loss</span>
              </div>
              <div className="tod">
                {slots.map((s) => (
                  <SlotRow key={s.slot} s={s} best={best?.slot === s.slot} />
                ))}
              </div>
            </section>
            <p className="note">Win rate per time slot, from every tracked match. Times are Brasília time (kick-off of each match).</p>
          </>
        );
      }}
    </Loaded>
  );
}
