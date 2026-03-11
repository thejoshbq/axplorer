import { Loader2, Play } from "lucide-react";
import { useDataStore } from "../../store/useDataStore";
import { useAnalysisStore } from "../../store/useAnalysisStore";
import { usePlotStore } from "../../store/usePlotStore";

const VIEW_LEVELS = ["Population", "Sample", "FOV"];

export function ControlsPanel() {
  const { availableEvents } = useDataStore();
  const a = useAnalysisStore();
  const { compute, computing } = usePlotStore();

  return (
    <div className="space-y-3">
      {/* Event selector */}
      <div>
        <label className="block text-xs text-[rgb(var(--color-text-secondary))] mb-1">Event</label>
        <select
          value={a.eventLabel}
          onChange={(e) => a.setEventLabel(e.target.value)}
          className="input-base w-full"
          disabled={availableEvents.length === 0}
        >
          <option value="">Select event...</option>
          {availableEvents.map((ev) => (
            <option key={ev} value={ev}>{ev}</option>
          ))}
        </select>
      </div>

      {/* View level */}
      <div>
        <label className="block text-xs text-[rgb(var(--color-text-secondary))] mb-1">View Level</label>
        <select value={a.viewLevel} onChange={(e) => a.setViewLevel(e.target.value)} className="input-base w-full">
          {VIEW_LEVELS.map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
      </div>

      <div className="neural-divider" />

      {/* Windows */}
      <div className="text-xs font-semibold text-[rgb(var(--color-text-secondary))]">Windows</div>
      <div>
        <label className="flex items-center justify-between text-xs text-theme-text/70 mb-1">
          <span>Pre-event (s)</span>
          <span className="text-accent">{a.preEventS.toFixed(1)}</span>
        </label>
        <input type="range" min="0.5" max="15" step="0.5" value={a.preEventS}
          onChange={(e) => a.setPreEventS(Number(e.target.value))}
          className="w-full accent-accent" />
      </div>
      <div>
        <label className="flex items-center justify-between text-xs text-theme-text/70 mb-1">
          <span>Post-event (s)</span>
          <span className="text-accent">{a.postEventS.toFixed(1)}</span>
        </label>
        <input type="range" min="0.5" max="30" step="0.5" value={a.postEventS}
          onChange={(e) => a.setPostEventS(Number(e.target.value))}
          className="w-full accent-accent" />
      </div>

      <div className="neural-divider" />

      {/* Preprocessing */}
      <div className="text-xs font-semibold text-[rgb(var(--color-text-secondary))]">Preprocessing</div>
      <label className="flex items-center gap-2 text-xs text-theme-text/80 cursor-pointer">
        <input type="checkbox" checked={a.enableDfof} onChange={(e) => a.setEnableDfof(e.target.checked)}
          className="accent-accent" />
        DF/F
      </label>
      {a.enableDfof && (
        <div>
          <label className="flex items-center justify-between text-xs text-theme-text/70 mb-1">
            <span>Percentile</span>
            <span className="text-accent">{a.dfofPercentile}</span>
          </label>
          <input type="range" min="1" max="50" step="1" value={a.dfofPercentile}
            onChange={(e) => a.setDfofPercentile(Number(e.target.value))}
            className="w-full accent-accent" />
        </div>
      )}
      <label className="flex items-center gap-2 text-xs text-theme-text/80 cursor-pointer">
        <input type="checkbox" checked={a.enableZscore} onChange={(e) => a.setEnableZscore(e.target.checked)}
          className="accent-accent" />
        Z-score
      </label>
      <label className="flex items-center gap-2 text-xs text-theme-text/80 cursor-pointer">
        <input type="checkbox" checked={a.enableSmooth} onChange={(e) => a.setEnableSmooth(e.target.checked)}
          className="accent-accent" />
        Smooth
      </label>
      {a.enableSmooth && (
        <div>
          <label className="flex items-center justify-between text-xs text-theme-text/70 mb-1">
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
      <div className="text-xs font-semibold text-[rgb(var(--color-text-secondary))]">Filtering</div>
      <div>
        <label className="block text-xs text-theme-text/70 mb-1">Buffer (ms)</label>
        <input type="number" min="0" value={a.bufferMs}
          onChange={(e) => a.setBufferMs(Number(e.target.value))}
          className="input-base w-full" />
      </div>
      <div>
        <label className="block text-xs text-theme-text/70 mb-1">Min Trials</label>
        <input type="number" min="1" value={a.minTrials}
          onChange={(e) => a.setMinTrials(Number(e.target.value))}
          className="input-base w-full" />
      </div>

      <div className="neural-divider" />

      {/* Heatmap */}
      <div className="text-xs font-semibold text-[rgb(var(--color-text-secondary))]">Heatmap</div>
      <label className="flex items-center gap-2 text-xs text-theme-text/80 cursor-pointer">
        <input type="checkbox" checked={a.enableHeatmap} onChange={(e) => a.setEnableHeatmap(e.target.checked)}
          className="accent-accent" />
        Show Heatmap
      </label>
      {a.enableHeatmap && (
        <div>
          <label className="block text-xs text-theme-text/70 mb-1">Sort Neurons</label>
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
        disabled={computing || !a.eventLabel}
        className="btn-sm w-full bg-accent text-accent-contrast font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
      >
        {computing ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
        {computing ? "Computing..." : "Compute"}
      </button>
    </div>
  );
}
