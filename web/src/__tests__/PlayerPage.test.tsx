import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { PlayerPage } from "../pages/PlayerPage";
import { Players } from "../pages/Players";
import type { PlayerDetail } from "../types";
import { PATH, REGINALDO, mockApi } from "./fixtures";

const DETAIL: PlayerDetail = {
  player: REGINALDO,
  history: [
    { matchId: "1", timestamp: "2026-10-29T21:00:00-03:00", rating: 8.4, goals: 1, assists: 2, motm: false },
    { matchId: "2", timestamp: "2026-10-29T22:36:40-03:00", rating: 9.9, goals: 2, assists: 2, motm: true },
  ],
  tracked: { games: 2, goals: 3, assists: 4, motm: 1, avgRating: 9.15 },
};

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/players" element={<Players />} />
        <Route path="/players/:gamertag" element={<PlayerPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

test("players grid sorted by goals", async () => {
  mockApi({ "/api/players": [PATH, REGINALDO] });
  renderAt("/players");
  const cards = await screen.findAllByRole("link");
  expect(cards[0]).toHaveTextContent("Reginaldo");
  expect(cards[1]).toHaveTextContent("Path");
});

test("player page shows every stat with plain labels", async () => {
  mockApi({ "/api/players/netozeraaa": DETAIL });
  renderAt("/players/netozeraaa");
  const club = await screen.findByTestId("at-club");
  for (const text of ["Games108", "Goals117", "Assists98", "Average rating8.2", "Man of the Match27",
    "Win rate51%", "Pass accuracy78%", "Passes made500", "Shot accuracy40%", "Tackles made40",
    "Tackle success35%", "Clean sheets0", "Red cards0"]) {
    expect(club).toHaveTextContent(text);
  }
});

test("player page shows tracked totals and recent matches", async () => {
  mockApi({ "/api/players/netozeraaa": DETAIL });
  renderAt("/players/netozeraaa");
  const tracked = await screen.findByTestId("tracked");
  expect(tracked).toHaveTextContent("Since tracking started");
  expect(tracked).toHaveTextContent("Games2");
  expect(tracked).toHaveTextContent("Avg rating9.15");
  expect(screen.getByTestId("history")).toHaveTextContent("9.9");
});

test("unknown player shows not found with link back", async () => {
  mockApi({ "/api/players/nope": { status: 404 } });
  renderAt("/players/nope");
  expect(await screen.findByText("Player not found")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /Back to players/ })).toHaveAttribute("href", "/players");
});
