import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import { AppRoutes } from "../App";

function mockFetch(routes: Record<string, unknown>) {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    const key = Object.keys(routes).find((k) => url.startsWith(k));
    if (!key) return new Response("{}", { status: 404 });
    return new Response(JSON.stringify(routes[key]), { status: 200 });
  });
}

test("tabs render and mark the active route", async () => {
  mockFetch({ "/api/status": { lastAttemptAt: null, lastSuccessAt: null, lastError: null }, "/api/players": [] });
  render(
    <MemoryRouter initialEntries={["/players"]}>
      <AppRoutes />
    </MemoryRouter>,
  );
  for (const name of ["Overview", "Players", "Matches", "Seasons"]) {
    expect(screen.getByRole("link", { name })).toBeInTheDocument();
  }
  expect(screen.getByRole("link", { name: "Players" })).toHaveAttribute("aria-current", "page");
  expect(screen.getByRole("link", { name: "Overview" })).not.toHaveAttribute("aria-current");
});
