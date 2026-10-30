import { Route, Routes } from "react-router-dom";
import { Header } from "./components/Header";
import { StateMessage } from "./components/StateMessage";
import { Tabs } from "./components/Tabs";
import { Matches } from "./pages/Matches";
import { Overview } from "./pages/Overview";
import { PlayerPage } from "./pages/PlayerPage";
import { Players } from "./pages/Players";
import { Seasons } from "./pages/Seasons";

export function AppRoutes() {
  return (
    <div className="wrap">
      <Header />
      <Tabs />
      <main>
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/players" element={<Players />} />
          <Route path="/players/:gamertag" element={<PlayerPage />} />
          <Route path="/matches" element={<Matches />} />
          <Route path="/seasons" element={<Seasons />} />
          <Route path="*" element={<StateMessage kind="not-found">Page not found.</StateMessage>} />
        </Routes>
      </main>
    </div>
  );
}
