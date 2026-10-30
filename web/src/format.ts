const TZ = "America/Sao_Paulo";

function parts(iso: string, opts: Intl.DateTimeFormatOptions) {
  const out: Record<string, string> = {};
  for (const p of new Intl.DateTimeFormat("en-GB", { timeZone: TZ, ...opts }).formatToParts(new Date(iso))) {
    out[p.type] = p.value;
  }
  return out;
}

/** "Thu 29 Oct" in São Paulo time. */
export function fmtDate(iso: string): string {
  const p = parts(iso, { weekday: "short", day: "numeric", month: "short" });
  return `${p.weekday} ${p.day} ${p.month}`;
}

/** "22:36" in São Paulo time. */
export function fmtTime(iso: string): string {
  const p = parts(iso, { hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
  return `${p.hour}:${p.minute}`;
}

export function ago(iso: string, now: Date = new Date()): string {
  const s = Math.max(0, (now.getTime() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  const d = Math.floor(s / 86400);
  return `${d} day${d === 1 ? "" : "s"} ago`;
}

export function pct(n: number | null | undefined): string {
  return n == null ? "–" : `${Math.round(n)}%`;
}

export const POSITION: Record<string, string> = {
  goalkeeper: "GK",
  defender: "DEF",
  midfielder: "MID",
  forward: "FWD",
};

export const posLabel = (p: string) => POSITION[p] ?? p.slice(0, 3).toUpperCase();
