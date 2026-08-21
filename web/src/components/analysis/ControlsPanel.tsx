import { useEffect } from "react";
import { Loader2, Play } from "lucide-react";
import { useDataStore } from "../../store/useDataStore";
import { useAnalysisStore } from "../../store/useAnalysisStore";
import { usePlotStore } from "../../store/usePlotStore";

export function ControlsPanel() {
  const { availableEvents, signalKind } = useDataStore();
  const a = useAnalysisStore();

  // Loaded signal is already DeltaF/F -- default the DF/F step off so it
  // isn't applied twice. Still user-overridable (the backend guards against
  // it anyway).
  useEffect(() => {
    if (signalKind === "dff") {
      a.setEnableDfof(false);
    }
  }, [signalKind]);

  const { compute, computing } = usePlotStore();

  return (
    <div className="space-y-s3">
      {/* Event selector -- multi-select: one population trace per checked event */}
      <div>
        <label className="block text-label text-ink-muted mb-s1">
          Events {a.eventLabels.length > 0 && `(${a.eventLabels.length} selected)`}
        </label>
        <div className="max-h-32 overflow-y-auto space-y-s1 border border-edge rounded px-s2 py-s1">
          {availableEvents.length === 0 && (
            <span className="text-label text-ink-faint">No events available.</span>
          )}
          {availableEvents.map((ev) => (
            <label key={ev} className="flex items-center gap-s2 text-label text-ink cursor-pointer">
              <input
                type="checkbox"
                checked={a.eventLabels.includes(ev)}
                onChange={() => a.toggleEventLabel(ev)}
                className="accent-accent"
              />
              {ev}
            </label>
          ))}
        </div>
      </div>

      <div className="neural-divider" />

      {/* Windows */}
      <div className="text-label font-semibold text-ink-muted">Windows</div>
      <div>
        <label className="flex items-center justify-between text-label text-ink-muted mb-s1">
          <span>Pre-event (s)</span>
          <span className="text-accent">{a.preEventS.toFixed(1)}</span>
        </label>
        <input type="range" min="0.5" max="15" step="0.5" value={a.preEventS}
          onChange={(e) => a.setPreEventS(Number(e.target.value))}
          className="w-full accent-accent" />
      </div>
      <div>
        <label className="flex items-center justify-between text-label text-ink-muted mb-s1">
          <span>Post-event (s)</span>
          <span className="text-accent">{a.postEventS.toFixed(1)}</span>
        </label>
        <input type="range" min="0.5" max="30" step="0.5" value={a.postEventS}
          onChange={(e) => a.setPostEventS(Number(e.target.value))}
          className="w-full accent-accent" />
      </div>

      <div className="neural-divider" />

      {/* Preprocessing */}
      <div className="text-label font-semibold text-ink-muted">Preprocessing</div>
      <label className="flex items-center gap-s2 text-label text-ink cursor-pointer">
        <input type="checkbox" checked={a.enableDfof} onChange={(e) => a.setEnableDfof(e.target.checked)}
          className="accent-accent" />
        DF/F
      </label>
      {signalKind === "dff" && (
        <p className="text-label text-ink-faint -mt-s1">
          Loaded signal is already ΔF/F -- defaulted off to avoid double-normalizing.
        </p>
      )}
      {a.enableDfof && (
        <div>
          <label className="flex items-center justify-between text-label text-ink-muted mb-s1">
            <span>Percentile</span>
            <span className="text-accent">{a.dfofPercentile}</span>
          </label>
          <input type="range" min="1" max="50" step="1" value={a.dfofPercentile}
            onChange={(e) => a.setDfofPercentile(Number(e.target.value))}
            className="w-full accent-accent" />
        </div>
      )}
      <label className="flex items-center gap-s2 text-label text-ink cursor-pointer">
        <input type="checkbox" checked={a.enableZscore} onChange={(e) => a.setEnableZscore(e.target.checked)}
          className="accent-accent" />
        Z-score
      </label>
      <label className="flex items-center gap-s2 text-label text-ink cursor-pointer">
        <input type="checkbox" checked={a.enableSmooth} onChange={(e) => a.setEnableSmooth(e.target.checked)}
          className="accent-accent" />
        Smooth
      </label>
      {a.enableSmooth && (
        <div>
          <label className="flex items-center justify-between text-label text-ink-muted mb-s1">
            <span>Sigma (frames)</span>
            <span className="text-accent">{a.smoothingSigma.toFixed(1)}</span>
          </label>
          <input type="range" min="0.5" max="5" step="0.5" value={a.smoothingSigma}
            onChange={(e) => a.setSmoothingSigma(Number(e.target.value))}
            className="w-full accent-accent" />
        </div>
      )}

      <div className="neural-divider" />

      {/* Filtering */}
      <div className="text-label font-semibold text-ink-muted">Filtering</div>
      <div>
        <label className="block text-label text-ink-muted mb-s1">Buffer (ms)</label>
        <input type="number" min="0" value={a.bufferMs}
          onChange={(e) => a.setBufferMs(Number(e.target.value))}
          className="input-base w-full" />
      </div>
      <div>
        <label className="block text-label text-ink-muted mb-s1">Min Trials</label>
        <input type="number" min="1" value={a.minTrials}
          onChange={(e) => a.setMinTrials(Number(e.target.value))}
          className="input-base w-full" />
      </div>

      <div className="neural-divider" />

      {/* Heatmap */}
      <div className="text-label font-semibold text-ink-muted">Heatmap</div>
      <label className="flex items-center gap-s2 text-label text-ink cursor-pointer">
        <input type="checkbox" checked={a.enableHeatmap} onChange={(e) => a.setEnableHeatmap(e.target.checked)}
          className="accent-accent" />
        Show Heatmap
      </label>
      {a.enableHeatmap && (
        <div>
          <label className="block text-label text-ink-muted mb-s1">Sort Neurons</label>
          <select value={a.sortMethod} onChange={(e) => a.setSortMethod(e.target.value)} className="input-base w-full">
            <option value="none">None</option>
            <option value="excitatory">Excitatory (peak latency)</option>
            <option value="inhibitory">Inhibitory (trough latency)</option>
            <option value="magnitude">Magnitude (abs peak)</option>
          </select>
        </div>
      )}

      <div className="neural-divider" />

      {/* Compute button */}
      <button
        onClick={compute}
        disabled={computing || a.eventLabels.length === 0}
        className="btn-sm w-full bg-accent text-accent-ink font-semibold flex items-center justify-center gap-s2 disabled:opacity-50"
      >
        {computing ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
        {computing ? "Computing..." : "Compute"}
      </button>
    </div>
  );
}
