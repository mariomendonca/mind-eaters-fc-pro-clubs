import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Insights } from "../pages/Insights";
import type { TimeOfDayResponse, TimeSlot } from "../types";
import { mockApi } from "./fixtures";

function slot(s: Partial<TimeSlot> & Pick<TimeSlot, "slot" | "label">): TimeSlot {
  return { startHour: 0, endHour: 0, games: 0, wins: 0, draws: 0, losses: 0, winRate: 0, ...s };
}

const DATA: TimeOfDayResponse = {
  slots: [
    slot({ slot: "morning", label: "Morning", startHour: 6, endHour: 12, games: 12, wins: 3, draws: 4, losses: 5, winRate: 25 }),
    slot({ slot: "afternoon", label: "Afternoon", startHour: 12, endHour: 18, games: 24, wins: 15, losses: 9, winRate: 62 }),
    slot({ slot: "night", label: "Night", startHour: 18, endHour: 6, games: 30, wins: 13, draws: 7, losses: 10, winRate: 43 }),
  ],
};

function renderPage() {
  return render(<MemoryRouter><Insights /></MemoryRouter>);
}

test("shows the record per time slot and highlights the best one", async () => {
  mockApi({ "/api/time-of-day": DATA });
  renderPage();
  expect(await screen.findByText("We win most in the afternoon")).toBeInTheDocument();
  expect(screen.getByTestId("record-morning")).toHaveTextContent("3W 4D 5L");
  expect(screen.getByTestId("slot-afternoon")).toHaveClass("best");
  expect(screen.getByTestId("slot-night")).not.toHaveClass("best");
  expect(screen.getByText("62%")).toBeInTheDocument();
});

test("no highlight when two slots tie", async () => {
  const tied = { slots: DATA.slots.map((s) => ({ ...s, winRate: 50 })) };
  mockApi({ "/api/time-of-day": tied });
  renderPage();
  expect(await screen.findByText("Win / draw / loss by time of day")).toBeInTheDocument();
  expect(screen.queryByText("Best time")).not.toBeInTheDocument();
});

test("no matches shows the no-data state", async () => {
  mockApi({ "/api/time-of-day": { slots: DATA.slots.map((s) => ({ ...s, games: 0, wins: 0, draws: 0, losses: 0, winRate: 0 })) } });
  renderPage();
  expect(await screen.findByText("No matches tracked yet.")).toBeInTheDocument();
});

