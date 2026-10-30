import { getPlayers } from "../api";
import { Loaded } from "../components/Loaded";
import { PlayerCard } from "../components/PlayerCard";
import { useLoad } from "../useLoad";

export function Players() {
  const state = useLoad(getPlayers);
  return (
    <Loaded state={state}>
      {(players) => (
        <section className="players" style={{ marginTop: 0 }}>
          {[...players]
            .sort((a, b) => b.goals - a.goals)
            .map((p, i) => (
              <PlayerCard key={p.gamertag} player={p} delay={i * 0.04} />
            ))}
        </section>
      )}
    </Loaded>
  );
}
