import { Link } from "react-router-dom";
import { posLabel } from "../format";
import type { Player } from "../types";

export function PlayerCard({ player, delay = 0 }: { player: Player; delay?: number }) {
  return (
    <Link to={`/players/${encodeURIComponent(player.gamertag)}`} className="pc" style={{ animationDelay: `${delay}s` }}>
      <div className="top">
        <div>
          <div className="ovr">{player.overall}</div>
          <div className="pos">{posLabel(player.position)}</div>
        </div>
        <span className="motm">⭐ {player.manOfTheMatch}</span>
      </div>
      <div className="nm">{player.displayName}</div>
      <div className="tag">
        {player.gamertag} · {player.gamesPlayed} games
      </div>
      <div className="stats">
        <div>
          <b>{player.goals}</b>
          <span>G</span>
        </div>
        <div>
          <b>{player.assists}</b>
          <span>A</span>
        </div>
        <div>
          <b>{player.averageRating.toFixed(1)}</b>
          <span>RAT</span>
        </div>
        <div>
          <b>{player.passSuccessRate}%</b>
          <span>PASS</span>
        </div>
      </div>
      <div className="bar">
        <i style={{ width: `${player.winRate}%` }} />
      </div>
      <div className="bl">
        <span>win rate</span>
        <span>{player.winRate}%</span>
      </div>
    </Link>
  );
}
