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

test("refresh button triggers api refresh", async () => {
  let calledRefresh = false;
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    if (url.includes("/api/refresh") && init?.method === "POST") {
      calledRefresh = true;
      return new Response(JSON.stringify({ status: "ok" }), { status: 200 });
    }
    return new Response("{}", { status: 200 });
  });

  render(
    <MemoryRouter initialEntries={["/"]}>
      <AppRoutes />
    </MemoryRouter>,
  );

  const btn = screen.getByRole("button", { name: "Refresh stats" });
  expect(btn).toBeInTheDocument();
  btn.click();
  await vi.waitFor(() => expect(calledRefresh).toBe(true));
});
