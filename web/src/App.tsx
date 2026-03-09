import { CyberpunkGridBackground } from "./components/layout/CyberpunkGridBackground";
import { CyberpunkCursor } from "./components/layout/CyberpunkCursor";
import { Header } from "./components/layout/Header";
import { Sidebar } from "./components/layout/Sidebar";
import { PlotGrid } from "./components/plots/PlotGrid";

export default function App() {
  return (
    <div className="flex flex-col h-screen">
      <CyberpunkGridBackground />
      <CyberpunkCursor />
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-6">
          <PlotGrid />
        </main>
      </div>
      <footer className="glass-panel border-t border-theme-border px-6 py-2 text-center">
        <span className="font-shareTechMono text-[0.6rem] tracking-[0.15em] uppercase text-accent/40">
          (c) 2026 LOGISTECH // ALL RIGHTS RESERVED // BUILD 2.0.0
        </span>
      </footer>
    </div>
  );
}
