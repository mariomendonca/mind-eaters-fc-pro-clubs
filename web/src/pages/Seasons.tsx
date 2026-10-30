import { getSeasons } from "../api";
import { Loaded } from "../components/Loaded";
import { StateMessage } from "../components/StateMessage";
import { fmtDate } from "../format";
import type { Campaign, EASeason, Leader, Outcome } from "../types";
import { useLoad } from "../useLoad";

const OUTCOME: Record<Outcome, string> = {
  promoted: "↑ Promoted",
  relegated: "↓ Relegated",
  stayed: "Stayed",
  in_progress: "In progress",
};

function Person({ label, leader }: { label: string; leader: Leader }) {
  return (
    <div className="stat">
      <span>{label}</span>
      <b className="person">{leader ? `${leader.displayName} · ${leader.value}` : "—"}</b>
    </div>
  );
}

function CampaignCard({ c, delay }: { c: Campaign; delay: number }) {
  const games = c.wins + c.draws + c.losses;
  return (
    <article className="campaign" data-testid="campaign" style={{ animationDelay: `${delay}s` }}>
      <div className="campaign-top">
        <div className="div-num">Div {c.division}</div>
        <span className={`pill ${c.outcome}`}>{OUTCOME[c.outcome]}</span>
      </div>
      <p className="campaign-record">
        {games} {games === 1 ? "game" : "games"} · {c.wins}W {c.draws}D {c.losses}L
      </p>
      <p className="muted campaign-meta">
        {c.goals} goals · {c.goalsAgainst} against · {fmtDate(c.startedAt)} – {c.endedAt ? fmtDate(c.endedAt) : "now"}
        {c.partial && " · since tracking started"}
      </p>
      <div className="stat-grid campaign-people">
        <Person label="Top scorer" leader={c.topScorer} />
        <Person label="Top MVP" leader={c.topMvp} />
      </div>
    </article>
  );
}

function SeasonBlock({ s, index }: { s: EASeason; index: number }) {
  const t = s.totals;
  return (
    <section className="card season-block" style={{ animationDelay: `${index * 0.06}s` }}>
      <h3>
        <span>
          EA season · {fmtDate(s.startedAt)} – {s.endedAt ? fmtDate(s.endedAt) : "now"}
        </span>
        {s.partial && <span className="pill in_progress">Since tracking started</span>}
      </h3>
      <p className="season-totals" data-testid="season-totals">
        {t.wins}W {t.ties}D {t.losses}L · {t.points} pts · {t.gamesPlayed} games · {t.goals}–{t.goalsAgainst} goals ·{" "}
        {t.promotions} promotions · {t.relegations} relegations
      </p>
      {s.promotionsBeforeTracking > 0 && (
        <p className="muted">
          {s.promotionsBeforeTracking} {s.promotionsBeforeTracking === 1 ? "promotion" : "promotions"} before tracking
        </p>
      )}
      <div className="campaigns">
        {s.campaigns.map((c, i) => (
          <CampaignCard key={c.startedAt + c.division} c={c} delay={0.1 + i * 0.05} />
        ))}
      </div>
    </section>
  );
}

export function Seasons() {
  const state = useLoad(getSeasons);
  return (
    <Loaded state={state}>
      {({ eaSeasons }) =>
        eaSeasons.length === 0 ? (
          <StateMessage kind="no-data" />
        ) : (
          <>
            {eaSeasons.map((s, i) => (
              <SeasonBlock key={s.startedAt} s={s} index={i} />
            ))}
            <p className="note">
              A new campaign starts each time the club changes division. Seasons and campaigns are tracked from 30 Oct 2026; earlier ones aren't
              known.
            </p>
          </>
        )
      }
    </Loaded>
  );
}
