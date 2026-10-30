import { vi } from "vitest";
import type { Match, Overview, Player } from "../types";

export function player(p: Partial<Player> & { gamertag: string; displayName: string }): Player {
  return {
    position: "midfielder", overall: 80, gamesPlayed: 50, winRate: 50, goals: 10, assists: 10,
    averageRating: 7.5, manOfTheMatch: 3, shotSuccessRate: 40, passesMade: 500, passSuccessRate: 75,
    tacklesMade: 40, tackleSuccessRate: 40, cleanSheetsDef: 0, cleanSheetsGK: 0, redCards: 0, ...p,
  };
}

export const REGINALDO = player({
  gamertag: "netozeraaa", displayName: "Reginaldo", position: "midfielder", overall: 82, gamesPlayed: 108,
  goals: 117, assists: 98, averageRating: 8.2, manOfTheMatch: 27, passSuccessRate: 78, winRate: 51, tackleSuccessRate: 35,
});
export const PATH = player({
  gamertag: "bielpontes04", displayName: "Path", position: "defender", overall: 82, gamesPlayed: 59,
  goals: 21, assists: 46, averageRating: 8.1, manOfTheMatch: 15, passSuccessRate: 83, winRate: 59,
});

export function match(m: Partial<Match> & { matchId: string }): Match {
  return {
    timestamp: "2026-10-29T22:36:40-03:00", opponentName: "Tamandua Xereka", opponentCrestUrl: "",
    goals: 6, goalsAgainst: 3, result: "win", dnf: false,
    motm: { gamertag: "bielpontes04", displayName: "Path" },
    best: { gamertag: "netozeraaa", displayName: "Reginaldo", rating: 10 }, ...m,
  };
}

export const OVERVIEW: Overview = {
  club: { clubId: 1232878, name: "Mind Eaters FC", crestUrl: "", stadium: "Estádio de ní", division: 4,
    bestDivision: 2, promotions: 6, relegations: 0, skillRating: 1782 },
  season: { gamesPlayed: 38, wins: 19, ties: 7, losses: 12, points: 28, goals: 120, goalsAgainst: 108 },
  allTime: { gamesPlayed: 123, wins: 63, ties: 15, losses: 45, goals: 360, goalsAgainst: 285, winStreak: 1, unbeatenStreak: 2 },
  recentMatches: [
    match({ matchId: "1" }),
    match({ matchId: "2", opponentName: "PASSARALHOO FC", goals: 2, goalsAgainst: 3, result: "loss", motm: null }),
    match({ matchId: "3", opponentName: "LAZIONADOS FC", goals: 5, goalsAgainst: 2, dnf: true }),
  ],
  mvpCounts: [{ gamertag: "bielpontes04", displayName: "Path", count: 2 }],
  leaders: {
    goals: { gamertag: "netozeraaa", displayName: "Reginaldo", value: 117 },
    assists: { gamertag: "netozeraaa", displayName: "Reginaldo", value: 98 },
    rating: { gamertag: "netozeraaa", displayName: "Reginaldo", value: 8.2 },
  },
  players: [REGINALDO, PATH],
  updatedAt: "2026-10-30T12:00:00-03:00",
};

export function mockApi(routes: Record<string, unknown | { status: number }>) {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    const key = Object.keys(routes).sort((a, b) => b.length - a.length).find((k) => url.startsWith(k));
    if (!key) return new Response("{}", { status: 404 });
    const value = routes[key] as { status?: number };
    if (value && typeof value === "object" && "status" in value && Object.keys(value).length === 1) {
      return new Response("{}", { status: value.status });
    }
    return new Response(JSON.stringify(value), { status: 200 });
  });
}
