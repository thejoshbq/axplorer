import { CyberpunkGridBackground } from "./components/layout/CyberpunkGridBackground";
import { Header } from "./components/layout/Header";
import { Sidebar } from "./components/layout/Sidebar";
import { PlotGrid } from "./components/plots/PlotGrid";

export default function App() {
  return (
    <div className="flex flex-col h-screen">
      <CyberpunkGridBackground />
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-s5">
          <PlotGrid />
        </main>
      </div>
      <footer className="phoxel-footer">
        (c) 2026 LOGISTECH // ALL RIGHTS RESERVED // BUILD {__APP_VERSION__}
      </footer>
    </div>
  );
}
