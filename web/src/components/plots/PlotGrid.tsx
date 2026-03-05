import { usePlotStore } from "../../store/usePlotStore";
import { PETHChart } from "./PETHChart";
import { Loader2 } from "lucide-react";

export function PlotGrid() {
  const { plots, yRange, eventLabel, computing, error } = usePlotStore();

  if (computing) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-[rgb(var(--color-text-secondary))]">
        <Loader2 size={32} className="animate-spin text-accent" />
        <span className="text-sm">Computing PETH...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-sm text-red-400 border border-red-400/20 bg-red-400/5 px-4 py-2 rounded">
          {error}
        </div>
      </div>
    );
  }

  if (plots.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-[rgb(var(--color-text-secondary))]">
        Load data and compute to view PETH plots.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-center text-sm font-semibold text-accent">
        PETH: {eventLabel}
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {plots.map((p, idx) => (
          <div key={idx} className="card">
            <PETHChart
              title={p.title}
              time={p.time}
              mean={p.mean}
              sem={p.sem}
              yRange={yRange}
              colorIndex={idx}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
