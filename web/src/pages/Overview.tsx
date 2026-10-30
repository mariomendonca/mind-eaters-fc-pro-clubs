import { getOverview } from "../api";
import { FormStrip } from "../components/FormStrip";
import { Leaders } from "../components/Leaders";
import { Loaded } from "../components/Loaded";
import { MatchRow } from "../components/MatchRow";
import { MvpBars } from "../components/MvpBars";
import { PlayerCard } from "../components/PlayerCard";
import { StatStrip } from "../components/StatStrip";
import { useLoad } from "../useLoad";

export function Overview() {
  const state = useLoad(getOverview);
  return (
    <Loaded state={state}>
      {(o) => (
        <>
          <StatStrip season={o.season} allTime={o.allTime} />
          <section className="grid2">
            <div className="card" style={{ animationDelay: ".2s" }} data-testid="recent-matches">
              <h3>
                Last {o.recentMatches.length} matches <small>league · newest first</small>
              </h3>
              <FormStrip matches={o.recentMatches} />
              {o.recentMatches.map((m) => (
                <MatchRow key={m.matchId} match={m} />
              ))}
            </div>
            <div className="card" style={{ animationDelay: ".28s" }}>
              <h3>
                Club leaders <small>all-time at the club</small>
              </h3>
              <Leaders leaders={o.leaders} />
              <h3 style={{ fontSize: 18 }}>
                MVPs <small>Man of the Match, last {o.recentMatches.length} matches</small>
              </h3>
              <MvpBars counts={o.mvpCounts} />
            </div>
          </section>
          <section className="players">
            {o.players.map((p, i) => (
              <PlayerCard key={p.gamertag} player={p} delay={0.34 + i * 0.04} />
            ))}
          </section>
          <p className="note">Player totals are their stats at the club. MVPs come from the most recent league matches.</p>
        </>
      )}
    </Loaded>
  );
}
