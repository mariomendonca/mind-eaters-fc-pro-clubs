import { useState } from "react";
import { getOverview, getStatus, postRefresh } from "../api";
import { ago } from "../format";
import { useLoad } from "../useLoad";

export function Header() {
  const overview = useLoad(getOverview);
  const status = useLoad(getStatus);
  const club = overview.kind === "ok" ? overview.data.club : null;
  const st = status.kind === "ok" ? status.data : null;
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);

  async function handleRefresh() {
    if (refreshing) return;
    setRefreshing(true);
    setRefreshError(null);
    try {
      await postRefresh();
    } catch (err: unknown) {
      setRefreshError(err instanceof Error ? err.message : "Refresh failed");
    } finally {
      setRefreshing(false);
    }
  }

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
          <span className="refresh-wrap">
            {st?.lastSuccessAt && (
              <span className={st.lastError ? "stale" : undefined} title={st.lastError ?? undefined}>
                updated {ago(st.lastSuccessAt)}
              </span>
            )}
            <button
              type="button"
              className={`refresh-btn ${refreshing ? "spinning" : ""}`}
              onClick={handleRefresh}
              disabled={refreshing}
              title={refreshError ?? (refreshing ? "Fetching latest data from EA…" : "Refresh stats from EA now")}
              aria-label="Refresh stats"
            >
              <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2" />
              </svg>
            </button>
            {refreshError && <span className="stale" style={{ fontSize: 12 }}>({refreshError})</span>}
          </span>
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
