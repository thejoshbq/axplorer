import { useRef, useState } from "react";
import { FolderOpen, Plus, Trash2, Upload, Loader2 } from "lucide-react";
import { api } from "../../api/client";
import { useDataStore } from "../../store/useDataStore";
import { StatusIndicator } from "./StatusIndicator";

const DATA_LEVELS = ["FOV", "Sample", "Population", "Project"];

export function UploadPanel() {
  const {
    source, setSource,
    dbPath, setDbPath,
    dataLevel, setDataLevel,
    paths, addPath, removePath,
    loadData, loading,
  } = useDataStore();
  const [pathInput, setPathInput] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleDbFilePick = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const { db_path } = await api.uploadDbFile(file);
      setUploadError(null);
      setDbPath(db_path);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

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

  const isDatabase = source === "database";

  return (
    <div className="space-y-3">
      {/* Source toggle */}
      <div>
        <label className="block text-xs text-[rgb(var(--color-text-secondary))] mb-1">Source</label>
        <div className="flex gap-1">
          {(["filesystem", "database"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setSource(s)}
              className={`flex-1 btn-sm capitalize ${
                source === s
                  ? "bg-accent text-accent-contrast font-semibold"
                  : "bg-panel border border-theme-border text-theme-text/70"
              }`}
            >
              {s === "filesystem" ? "File System" : "Database"}
            </button>
          ))}
        </div>
      </div>

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

      {isDatabase ? (
        <>
          <div>
            <label className="block text-xs text-[rgb(var(--color-text-secondary))] mb-1">
              DB Path <span className="opacity-50">(optional)</span>
            </label>
            <div className="flex gap-1">
              <input
                type="text"
                value={dbPath}
                onChange={(e) => setDbPath(e.target.value)}
                placeholder="~/.pynapse/pynapse.duckdb"
                className="input-base flex-1 min-w-0"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="btn-sm bg-panel border border-theme-border text-accent disabled:opacity-50"
                title="Browse for .duckdb file"
              >
                {uploading ? <Loader2 size={14} className="animate-spin" /> : <FolderOpen size={14} />}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".duckdb"
                className="hidden"
                onChange={handleDbFilePick}
              />
            </div>
            {uploadError && (
              <p className="text-xs text-red-400 mt-0.5">{uploadError}</p>
            )}
          </div>

          <div>
            <label className="block text-xs text-[rgb(var(--color-text-secondary))] mb-1">
              {dataLevel} Name(s)
            </label>
            <div className="flex gap-1">
              <input
                type="text"
                value={pathInput}
                onChange={(e) => setPathInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={`Enter ${dataLevel.toLowerCase()} name`}
                className="input-base flex-1 min-w-0"
              />
              <button
                onClick={handleAdd}
                className="btn-sm bg-panel border border-theme-border text-accent"
                title="Add name"
              >
                <Plus size={14} />
              </button>
            </div>
          </div>
        </>
      ) : (
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
            <button
              onClick={handleAdd}
              className="btn-sm bg-panel border border-theme-border text-accent"
              title="Add path"
            >
              <Plus size={14} />
            </button>
          </div>
        </div>
      )}

      {paths.length > 0 && (
        <div className="space-y-1">
          <label className="block text-xs text-[rgb(var(--color-text-secondary))]">
            {isDatabase ? "Queued Names" : "Queued Paths"}
          </label>
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
