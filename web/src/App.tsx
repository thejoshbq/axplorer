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
      <footer className="bg-surface-2 border-t border-edge px-s5 py-s2 text-center">
        <span className="font-ui text-micro tracking-caps uppercase text-ink-faint">
          (c) 2026 LOGISTECH // ALL RIGHTS RESERVED // BUILD 2.0.0
        </span>
      </footer>
    </div>
  );
}
