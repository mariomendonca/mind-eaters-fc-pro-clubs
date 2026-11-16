import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Archetypes } from "../pages/Archetypes";
import type { ArchetypesResponse } from "../types";
import { mockApi } from "./fixtures";

const row = (gamertag: string, displayName: string, x: Partial<ArchetypesResponse["archetypes"][0]["players"][0]>) => ({
  gamertag, displayName, games: 10, wins: 5, draws: 2, losses: 3, goals: 10, assists: 4, motm: 2, avgRating: 7.5,
  lastPlayed: "2026-11-03T13:52:20-03:00", ...x,
});

const DATA: ArchetypesResponse = {
  archetypes: [
    { id: 12, name: "Finisher", games: 63, wins: 30, draws: 11, losses: 22, winRate: 48, playerGames: 64, goals: 69, assists: 33, motm: 20,
      avgRating: 7.75, players: [
        row("CUFIS", "A. Rufino", { games: 35, wins: 16, draws: 7, losses: 12, goals: 26, avgRating: 7.24 }),
        row("bielpontes04", "Path", { games: 28, wins: 14, draws: 5, losses: 9, goals: 43, avgRating: 8.23 }),
      ] },
    { id: 8, name: "Maestro", games: 34, wins: 20, draws: 3, losses: 11, winRate: 59, playerGames: 34, goals: 8, assists: 25, motm: 5,
      avgRating: 7.74, players: [row("netozeraaa", "Reginaldo", { games: 34, wins: 20, draws: 3, losses: 11 })] },
  ],
  unused: ["Boss", "Magician"],
};

function renderPage() {
  return render(<MemoryRouter><Archetypes /></MemoryRouter>);
}

test("one card per archetype with the team record", async () => {
  mockApi({ "/api/archetypes": DATA });
  renderPage();
  expect(await screen.findByTestId("archetype-record-12")).toHaveTextContent("Team: 30W 11D 22L · 63 games");
  expect(screen.getByTestId("archetype-8")).toHaveTextContent("59%");
});

test("each archetype lists its players with their own numbers", async () => {
  mockApi({ "/api/archetypes": DATA });
  renderPage();
  const rows = within(await screen.findByTestId("archetype-12")).getAllByRole("row").slice(1);
  expect(rows).toHaveLength(2);
  expect(rows[1]).toHaveTextContent(/Path\s*28\s*14-5-9\s*50%\s*43/);
  expect(rows[1]).toHaveTextContent("1.54"); // goals per game
  expect(within(rows[1]).getByRole("link", { name: "Path" })).toHaveAttribute("href", "/players/bielpontes04");
});

test("lists archetypes nobody has played yet", async () => {
  mockApi({ "/api/archetypes": DATA });
  renderPage();
  expect(await screen.findByTestId("unused")).toHaveTextContent("Not played yet: Boss, Magician");
});

test("empty state", async () => {
  mockApi({ "/api/archetypes": { archetypes: [], unused: [] } });
  renderPage();
  expect(await screen.findByText("No archetypes in the saved matches yet.")).toBeInTheDocument();
});
