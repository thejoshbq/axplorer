import { useState } from "react";
import { FolderOpen, Upload, Loader2 } from "lucide-react";
import { useDataStore } from "../../store/useDataStore";
import { StatusIndicator } from "./StatusIndicator";
import { FileBrowser } from "./FileBrowser";

type BrowseTarget = "trace" | "event" | "frameTimestamps" | null;

const BROWSE_FILE_TYPES: Record<Exclude<BrowseTarget, null>, string[]> = {
  trace: ["npy", "h5"],
  event: ["csv", "mat", "xlsx"],
  frameTimestamps: ["csv"],
};

export function UploadPanel() {
  const {
    tracePath, setTracePath,
    eventPath, setEventPath,
    frameTimestampsPath, setFrameTimestampsPath,
    loadData, loading,
    availableH5Kinds, h5Kind, setH5Kind,
    lastDir, setLastDir,
  } = useDataStore();
  const [browseTarget, setBrowseTarget] = useState<BrowseTarget>(null);

  const handleBrowseSelect = (selectedPaths: string[]) => {
    const path = selectedPaths[0];
    if (!path) return;
    if (browseTarget === "trace") setTracePath(path);
    else if (browseTarget === "event") setEventPath(path);
    else if (browseTarget === "frameTimestamps") setFrameTimestampsPath(path);
  };

  const canLoad =
    tracePath.length > 0 &&
    eventPath.length > 0 &&
    !(availableH5Kinds.length > 0 && !h5Kind);

  return (
    <div className="space-y-s3">
      <div>
        <label className="block text-label text-ink-muted mb-s1">
          Neural Trace File <span className="text-ink-faint">(.npy / .h5)</span>
        </label>
        <div className="flex gap-s1">
          <input
            type="text"
            value={tracePath}
            onChange={(e) => setTracePath(e.target.value)}
            placeholder="/path/to/extractedsignals_raw.npy"
            className="input-base flex-1 min-w-0"
          />
          <button
            onClick={() => setBrowseTarget("trace")}
            className="btn-sm bg-surface-1 border border-edge text-accent"
            title="Browse filesystem"
          >
            <FolderOpen size={14} />
          </button>
        </div>
      </div>

      {availableH5Kinds.length > 0 && (
        <div>
          <label className="block text-label text-ink-muted mb-s1">
            Trace Kind <span className="text-ink-faint">(required for .h5 sources)</span>
          </label>
          <select
            value={h5Kind ?? ""}
            onChange={(e) => setH5Kind(e.target.value || null)}
            className="input-base w-full"
          >
            <option value="">Select trace kind...</option>
            {availableH5Kinds.map((k) => (
              <option key={k} value={k}>{k}</option>
            ))}
          </select>
        </div>
      )}

      <div>
        <label className="block text-label text-ink-muted mb-s1">
          Behavior Event File <span className="text-ink-faint">(.csv / .mat / .xlsx)</span>
        </label>
        <div className="flex gap-s1">
          <input
            type="text"
            value={eventPath}
            onChange={(e) => setEventPath(e.target.value)}
            placeholder="/path/to/behavior_events.csv"
            className="input-base flex-1 min-w-0"
          />
          <button
            onClick={() => setBrowseTarget("event")}
            className="btn-sm bg-surface-1 border border-edge text-accent"
            title="Browse filesystem"
          >
            <FolderOpen size={14} />
          </button>
        </div>
      </div>

      <div>
        <label className="block text-label text-ink-muted mb-s1">
          Frame Timestamps <span className="text-ink-faint">(optional -- must be named frame_timestamps.csv)</span>
        </label>
        <div className="flex gap-s1">
          <input
            type="text"
            value={frameTimestampsPath}
            onChange={(e) => setFrameTimestampsPath(e.target.value)}
            placeholder="/path/to/frame_timestamps.csv"
            className="input-base flex-1 min-w-0"
          />
          <button
            onClick={() => setBrowseTarget("frameTimestamps")}
            className="btn-sm bg-surface-1 border border-edge text-accent"
            title="Browse filesystem"
          >
            <FolderOpen size={14} />
          </button>
        </div>
      </div>

      <button
        onClick={loadData}
        disabled={loading || !canLoad}
        className="btn-sm w-full bg-accent text-accent-ink font-semibold flex items-center justify-center gap-s2 disabled:opacity-50"
      >
        {loading ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
        {loading ? "Loading..." : "Load Data"}
      </button>

      <StatusIndicator />

      <FileBrowser
        open={browseTarget !== null}
        onClose={() => setBrowseTarget(null)}
        onSelect={handleBrowseSelect}
        multiSelect={false}
        fileTypes={browseTarget ? BROWSE_FILE_TYPES[browseTarget] : undefined}
        initialPath={lastDir ?? undefined}
        onNavigate={setLastDir}
      />
    </div>
  );
}
