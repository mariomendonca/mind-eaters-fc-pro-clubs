import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Opponents } from "../pages/Opponents";
import type { Opponent } from "../types";
import { match, mockApi } from "./fixtures";

function opp(o: Partial<Opponent> & { name: string }): Opponent {
  return { opponentId: Math.random(), crestUrl: "", games: 1, wins: 1, draws: 0, losses: 0, goals: 2, goalsAgainst: 1,
    lastPlayed: "2026-11-03T13:52:20-03:00", matches: [match({ matchId: `${o.name}-1`, opponentName: o.name })], ...o };
}

const DATA: Opponent[] = [
  opp({ name: "Tropa do erro", games: 2, wins: 2, matches: [match({ matchId: "t1", opponentName: "Tropa do erro" }), match({ matchId: "t2", opponentName: "Tropa do erro" })] }),
  opp({ name: "VIDA RASA", games: 2, wins: 0, losses: 2 }),
  opp({ name: "São Caetano", wins: 0, draws: 1 }),
  opp({ name: "Favela Team" }),
];

function renderPage() {
  return render(<MemoryRouter><Opponents /></MemoryRouter>);
}

const names = () => screen.getAllByTestId("opponent").map((el) => within(el).getByRole("button").textContent);

test("lists every opponent with its record", async () => {
  mockApi({ "/api/opponents": DATA });
  renderPage();
  expect(await screen.findByText("4 clubs faced")).toBeInTheDocument();
  expect(screen.getAllByTestId("opponent")).toHaveLength(4);
  expect(screen.getAllByTestId("opponent")[1]).toHaveTextContent("0W 0D 2L");
});

test("search ignores case and accents", async () => {
  mockApi({ "/api/opponents": DATA });
  renderPage();
  fireEvent.change(await screen.findByLabelText("Search team"), { target: { value: "sao" } });
  expect(names()).toHaveLength(1);
  expect(names()[0]).toContain("São Caetano");
  fireEvent.change(screen.getByLabelText("Search team"), { target: { value: "zzz" } });
  expect(screen.getByText("No teams match.")).toBeInTheDocument();
});

test("rematch filter keeps only teams played more than once", async () => {
  mockApi({ "/api/opponents": DATA });
  renderPage();
  fireEvent.click(await screen.findByRole("button", { name: "Played 2+ times (2)" }));
  expect(names()).toHaveLength(2);
  expect(names().join()).not.toContain("Favela");
});

test("clicking a team shows its matches", async () => {
  mockApi({ "/api/opponents": DATA });
  renderPage();
  const row = (await screen.findAllByTestId("opponent"))[0];
  fireEvent.click(within(row).getAllByRole("button")[0]);
  expect(within(row).getAllByText("Tropa do erro")).toHaveLength(3); // header + 2 matches
});
