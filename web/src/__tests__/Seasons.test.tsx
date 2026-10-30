import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Seasons } from "../pages/Seasons";
import type { Campaign, SeasonsResponse } from "../types";
import { mockApi } from "./fixtures";

function campaign(c: Partial<Campaign>): Campaign {
  return { division: 4, startedAt: "2026-10-30T12:00:00-03:00", endedAt: null, outcome: "in_progress", partial: false,
    wins: 6, draws: 2, losses: 2, goals: 33, goalsAgainst: 25,
    topScorer: { gamertag: "CUFIS", displayName: "A. Rufino", value: 12 },
    topMvp: { gamertag: "bielpontes04", displayName: "Path", value: 4 }, ...c };
}

const DATA: SeasonsResponse = {
  eaSeasons: [{
    startedAt: "2026-10-30T12:00:00-03:00", endedAt: null, partial: true, promotionsBeforeTracking: 2,
    totals: { gamesPlayed: 38, wins: 19, ties: 7, losses: 12, points: 28, goals: 120, goalsAgainst: 108, promotions: 2, relegations: 0 },
    campaigns: [
      campaign({ division: 3, outcome: "in_progress" }),
      campaign({ division: 4, outcome: "promoted", partial: true, endedAt: "2026-11-02T12:00:00-03:00" }),
      campaign({ division: 3, outcome: "relegated", topScorer: null, topMvp: null }),
      campaign({ division: 3, outcome: "stayed" }),
    ],
  }],
};

function renderPage() {
  return render(<MemoryRouter><Seasons /></MemoryRouter>);
}

test("partial season shows tracking notes and totals", async () => {
  mockApi({ "/api/seasons": DATA });
  renderPage();
  expect(await screen.findByText("Since tracking started")).toBeInTheDocument();
  expect(screen.getByText("2 promotions before tracking")).toBeInTheDocument();
  expect(screen.getByTestId("season-totals")).toHaveTextContent("19W 7D 12L · 28 pts");
});

test("outcome pills render for all four outcomes", async () => {
  mockApi({ "/api/seasons": DATA });
  renderPage();
  expect(await screen.findByText("In progress")).toBeInTheDocument();
  expect(screen.getByText("↑ Promoted")).toBeInTheDocument();
  expect(screen.getByText("↓ Relegated")).toBeInTheDocument();
  expect(screen.getByText("Stayed")).toBeInTheDocument();
});

test("campaign card shows record, scorer and partial note", async () => {
  mockApi({ "/api/seasons": DATA });
  renderPage();
  const cards = await screen.findAllByTestId("campaign");
  expect(cards[0]).toHaveTextContent("Div 3");
  expect(cards[0]).toHaveTextContent("10 games · 6W 2D 2L");
  expect(cards[0]).toHaveTextContent("A. Rufino");
  expect(cards[1]).toHaveTextContent("since tracking started");
  expect(cards[2]).toHaveTextContent("—");
});

test("empty seasons", async () => {
  mockApi({ "/api/seasons": { eaSeasons: [] } });
  renderPage();
  expect(await screen.findByText("Collecting the first data from EA… check back in a few minutes.")).toBeInTheDocument();
});
