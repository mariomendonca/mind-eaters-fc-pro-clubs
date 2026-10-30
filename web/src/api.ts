import type { MatchDetail, MatchesResponse, Overview, Player, PlayerDetail, SeasonsResponse, Status } from "./types";

export class NoDataYet extends Error {}
export class NotFound extends Error {}

const TTL_MS = 30_000;
const cache = new Map<string, { at: number; promise: Promise<unknown> }>();

async function request<T>(path: string): Promise<T> {
  const res = await fetch(`/api${path}`);
  if (res.status === 503) throw new NoDataYet("no data yet");
  if (res.status === 404) throw new NotFound(path);
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${path}`);
  return (await res.json()) as T;
}

/** Shares one request between components that ask for the same data at once. */
function get<T>(path: string): Promise<T> {
  const hit = cache.get(path);
  if (hit && Date.now() - hit.at < TTL_MS) return hit.promise as Promise<T>;
  const promise = request<T>(path);
  cache.set(path, { at: Date.now(), promise });
  promise.catch(() => cache.delete(path));
  return promise;
}

export function clearCache() {
  cache.clear();
}

export const getOverview = () => get<Overview>("/overview");
export const getPlayers = () => get<Player[]>("/players");
export const getPlayer = (tag: string) => get<PlayerDetail>(`/players/${encodeURIComponent(tag)}`);
export const getMatches = (limit = 100) => get<MatchesResponse>(`/matches?limit=${limit}`);
export const getMatch = (id: string) => get<MatchDetail>(`/matches/${encodeURIComponent(id)}`);
export const getSeasons = () => get<SeasonsResponse>("/seasons");
export const getStatus = () => get<Status>("/status");
