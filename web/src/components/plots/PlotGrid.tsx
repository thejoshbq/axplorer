import { usePlotStore } from "../../store/usePlotStore";
import { PETHChart } from "./PETHChart";
import { HeatmapChart } from "./HeatmapChart";
import { Loader2 } from "lucide-react";

export function PlotGrid() {
  const { plots, yRange, zRange, eventLabels, dfofSkippedReason, computing, error } = usePlotStore();

  if (computing) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-s3 text-ink-muted">
        <Loader2 size={32} className="animate-spin text-accent" />
        <span className="text-body">Computing PETH...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-body text-err border border-err/20 bg-err/5 px-s4 py-s2 rounded">
          {error}
        </div>
      </div>
    );
  }

  if (plots.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-body text-ink-muted">
        Load data and compute to view PETH plots.
      </div>
    );
  }

  return (
    <div className="space-y-s4">
      <h3 className="text-center text-body font-semibold text-accent">
        PETH: {eventLabels.join(", ")}
      </h3>
      <p className="text-center text-label text-ink-muted">
        Population trace shows mean and median. Mode is not shown -- not meaningful for continuous ΔF/F signals.
      </p>
      {dfofSkippedReason && (
        <p className="text-center text-label text-warn">{dfofSkippedReason}</p>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-s4">
        {plots.map((p, idx) => (
          <div key={idx} className="card">
            <PETHChart
              title={p.title}
              time={p.time}
              mean={p.mean}
              median={p.median}
              sem={p.sem}
              yRange={yRange}
              colorIndex={idx}
            />
            {p.heatmap && (
              <HeatmapChart heatmap={p.heatmap} time={p.time} zRange={zRange} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
