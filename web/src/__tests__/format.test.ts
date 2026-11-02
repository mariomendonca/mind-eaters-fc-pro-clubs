import { ago, fmtDate, fmtTime, perGame } from "../format";

test("ago", () => {
  const now = new Date("2026-10-30T12:00:00-03:00");
  expect(ago("2026-10-30T11:55:00-03:00", now)).toBe("5 min ago");
  expect(ago("2026-10-30T09:00:00-03:00", now)).toBe("3 h ago");
  expect(ago("2026-10-28T11:00:00-03:00", now)).toBe("2 days ago");
  expect(ago("2026-10-30T11:59:40-03:00", now)).toBe("just now");
});

test("fmtDate uses São Paulo time", () => {
  expect(fmtDate("2026-10-30T01:30:00Z")).toBe("Thu 29 Oct");
});

test("fmtTime uses São Paulo time", () => {
  expect(fmtTime("2026-10-30T01:36:40Z")).toBe("22:36");
});

test("perGame rounds to two decimals and handles no games", () => {
  expect(perGame(117, 108)).toBe("1.08");
  expect(perGame(4, 2)).toBe("2.00");
  expect(perGame(5, 0)).toBe("–");
  expect(perGame(null, 10)).toBe("–");
});
