import { getOverview, getStatus } from "../api";
import { ago } from "../format";
import { useLoad } from "../useLoad";

export function Header() {
  const overview = useLoad(getOverview);
  const status = useLoad(getStatus);
  const club = overview.kind === "ok" ? overview.data.club : null;
  const st = status.kind === "ok" ? status.data : null;

  return (
    <header className="masthead">
      <div className="crest">{club?.crestUrl ? <img src={club.crestUrl} alt="" /> : <span>ME</span>}</div>
      <div>
        <h1>
          Mind <em>Eaters</em> FC
        </h1>
        <div className="sub">
          {club && (
            <>
              <span>
                Division <b>{club.division}</b> · best <b>Div {club.bestDivision}</b>
              </span>
              <span>
                <b>{club.promotions}</b> promotions · <b>{club.relegations}</b> relegations
              </span>
              {club.stadium && <span>{club.stadium}</span>}
            </>
          )}
          {st?.lastSuccessAt && (
            <span className={st.lastError ? "stale" : undefined} title={st.lastError ?? undefined}>
              updated {ago(st.lastSuccessAt)}
            </span>
          )}
        </div>
      </div>
      {club && (
        <div className="sr">
          <div className="label">Skill rating</div>
          <div className="big">{club.skillRating}</div>
        </div>
      )}
    </header>
  );
}
