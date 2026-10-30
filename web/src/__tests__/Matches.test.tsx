import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { Matches } from "../pages/Matches";
import type { MatchDetail, MatchesResponse } from "../types";
import { match, mockApi } from "./fixtures";

const M1 = match({ matchId: "151090313490136" });
const LIST: MatchesResponse = {
  sessions: [{ start: "2026-10-29T19:37:00-03:00", wins: 7, draws: 2, losses: 1, matches: [M1, match({ matchId: "2", opponentName: "Bodao EC", result: "loss", goals: 1, goalsAgainst: 4, motm: null })] }],
  nextBefore: null,
};
const DETAIL: MatchDetail = {
  match: M1,
  players: [
    { gamertag: "netozeraaa", displayName: "Reginaldo", position: "midfielder", rating: 10, goals: 0, assists: 0, shots: 0,
      passesMade: 0, passAttempts: 0, tacklesMade: 0, tackleAttempts: 0, saves: 0, manOfTheMatch: false, secondsPlayed: 4549 },
    { gamertag: "bielpontes04", displayName: "Path", position: "defender", rating: 9.5, goals: 1, assists: 3, shots: 2,
      passesMade: 30, passAttempts: 34, tacklesMade: 5, tackleAttempts: 8, saves: 0, manOfTheMatch: true, secondsPlayed: 5400 },
  ],
};

function renderPage() {
  return render(
    <MemoryRouter>
      <Matches />
    </MemoryRouter>,
  );
}

test("session header shows date and record", async () => {
  mockApi({ "/api/matches?": { ...LIST, nextBefore: null } });
  renderPage();
  expect(await screen.findByText("Thu 29 Oct · 7W 2D 1L")).toBeInTheDocument();
  expect(screen.getByText("Bodao EC")).toBeInTheDocument();
});

test("clicking a match shows the player table", async () => {
  mockApi({ "/api/matches?": { ...LIST, nextBefore: null }, "/api/matches/151090313490136": DETAIL });
  renderPage();
  await userEvent.click(await screen.findByRole("button", { name: /Tamandua Xereka/ }));
  const table = await screen.findByRole("table");
  const rows = within(table).getAllByRole("row");
  expect(rows[1]).toHaveTextContent("Reginaldo");
  expect(rows[1]).toHaveTextContent("76");
  expect(rows[2]).toHaveClass("is-motm");
  expect(rows[2]).toHaveTextContent("30/34");
});

test("empty history message", async () => {
  mockApi({ "/api/matches?": { sessions: [], nextBefore: null } });
  renderPage();
  expect(await screen.findByText(/No matches saved yet/)).toBeInTheDocument();
});

test("load older appends the next page", async () => {
  const older: MatchesResponse = {
    sessions: [{ start: "2026-10-20T20:00:00-03:00", wins: 0, draws: 0, losses: 1, matches: [match({ matchId: "9", opponentName: "Ancient FC", result: "loss" })] }],
    nextBefore: null,
  };
  mockApi({ "/api/matches?limit=50&before=": older, "/api/matches?": { ...LIST, nextBefore: "2026-10-29T19:37:00-03:00" } });
  renderPage();
  await userEvent.click(await screen.findByRole("button", { name: "Load older matches" }));
  expect(await screen.findByText("Ancient FC")).toBeInTheDocument();
  expect(screen.getByText("Tamandua Xereka")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Load older matches" })).not.toBeInTheDocument();
});
