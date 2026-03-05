import { useState } from "react";
import { Plus, Trash2, Upload, Loader2 } from "lucide-react";
import { useDataStore } from "../../store/useDataStore";
import { StatusIndicator } from "./StatusIndicator";

const DATA_LEVELS = ["FOV", "Sample", "Population", "Project"];

export function UploadPanel() {
  const { dataLevel, setDataLevel, paths, addPath, removePath, loadData, loading } = useDataStore();
  const [pathInput, setPathInput] = useState("");

  const handleAdd = () => {
    const trimmed = pathInput.trim();
    if (trimmed) {
      addPath(trimmed);
      setPathInput("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleAdd();
  };

  return (
    <div className="space-y-3">
      <div>
        <label className="block text-xs text-[rgb(var(--color-text-secondary))] mb-1">Data Level</label>
        <select
          value={dataLevel}
          onChange={(e) => setDataLevel(e.target.value)}
          className="input-base w-full"
        >
          {DATA_LEVELS.map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-xs text-[rgb(var(--color-text-secondary))] mb-1">Path</label>
        <div className="flex gap-1">
          <input
            type="text"
            value={pathInput}
            onChange={(e) => setPathInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="/path/to/data"
            className="input-base flex-1 min-w-0"
          />
          <button onClick={handleAdd} className="btn-sm bg-panel border border-theme-border text-accent" title="Add path">
            <Plus size={14} />
          </button>
        </div>
      </div>

      {paths.length > 0 && (
        <div className="space-y-1">
          <label className="block text-xs text-[rgb(var(--color-text-secondary))]">Queued Paths</label>
          <div className="max-h-28 overflow-y-auto space-y-1">
            {paths.map((p) => (
              <div key={p} className="flex items-center gap-1 group">
                <span className="flex-1 text-xs truncate text-theme-text/70" title={p}>{p}</span>
                <button
                  onClick={() => removePath(p)}
                  className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 transition-opacity"
                  title="Remove"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <button
        onClick={loadData}
        disabled={loading || paths.length === 0}
        className="btn-sm w-full bg-accent text-accent-contrast font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
      >
        {loading ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
        {loading ? "Loading..." : "Load Data"}
      </button>

      <StatusIndicator />
    </div>
  );
}
