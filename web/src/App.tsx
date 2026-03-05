import { NeonGridBackground } from "./components/layout/NeonGridBackground";
import { Header } from "./components/layout/Header";
import { Sidebar } from "./components/layout/Sidebar";
import { PlotGrid } from "./components/plots/PlotGrid";

export default function App() {
  return (
    <div className="flex flex-col h-screen">
      <NeonGridBackground />
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-6">
          <PlotGrid />
        </main>
      </div>
    </div>
  );
}
