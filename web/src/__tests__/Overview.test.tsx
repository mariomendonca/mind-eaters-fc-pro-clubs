import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Overview } from "../pages/Overview";
import { OVERVIEW, mockApi } from "./fixtures";

function renderPage() {
  return render(
    <MemoryRouter>
      <Overview />
    </MemoryRouter>,
  );
}

test("shows season record and points", async () => {
  mockApi({ "/api/overview": OVERVIEW });
  renderPage();
  const season = await screen.findByTestId("season-tile");
  expect(season).toHaveTextContent("19W 7D 12L");
  expect(season).toHaveTextContent("28 pts · 38 games");
  const strip = within(season.parentElement!);
  expect(strip.getByText("51%")).toBeInTheDocument();
  expect(strip.getByText("+75")).toBeInTheDocument();
});

test("shows MOTM or 'no MOTM' per match", async () => {
  mockApi({ "/api/overview": OVERVIEW });
  renderPage();
  const list = await screen.findByTestId("recent-matches");
  expect(within(list).getAllByText("⭐ Path").length).toBe(2);
  expect(within(list).getByText("no MOTM")).toBeInTheDocument();
});

test("shows DNF tag", async () => {
  mockApi({ "/api/overview": OVERVIEW });
  renderPage();
  expect(await screen.findByText("DNF")).toBeInTheDocument();
});

test("player card shows displayName and gamertag and links to the player", async () => {
  mockApi({ "/api/overview": OVERVIEW });
  renderPage();
  const card = await screen.findByRole("link", { name: /Reginaldo/ });
  expect(card).toHaveTextContent("netozeraaa · 108 games");
  expect(card).toHaveTextContent("MID");
  expect(card).toHaveTextContent("⭐ 27");
  expect(card).toHaveAttribute("href", "/players/netozeraaa");
});

test("503 shows collecting message", async () => {
  mockApi({ "/api/overview": { status: 503 } });
  renderPage();
  expect(await screen.findByText("Collecting the first data from EA… check back in a few minutes.")).toBeInTheDocument();
});
