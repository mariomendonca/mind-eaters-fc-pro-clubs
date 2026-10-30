import { NavLink } from "react-router-dom";

const TABS = [
  { to: "/", label: "Overview", end: true },
  { to: "/players", label: "Players", end: false },
  { to: "/matches", label: "Matches", end: false },
  { to: "/seasons", label: "Seasons", end: false },
];

export function Tabs() {
  return (
    <nav className="tabs" aria-label="Sections">
      {TABS.map((t) => (
        <NavLink key={t.to} to={t.to} end={t.end} className={({ isActive }) => (isActive ? "on" : undefined)}>
          {t.label}
        </NavLink>
      ))}
    </nav>
  );
}
