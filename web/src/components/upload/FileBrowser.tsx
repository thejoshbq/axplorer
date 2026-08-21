import { useCallback, useEffect, useState } from "react";
import {
  ArrowUp,
  Database,
  File,
  FileSpreadsheet,
  Folder,
  Table,
  X,
} from "lucide-react";
import { api } from "../../api/client";

interface BrowseEntry {
  name: string;
  path: string;
  type: string;
  size: number | null;
}

interface BrowseResponse {
  current: string;
  parent: string | null;
  entries: BrowseEntry[];
}

const ICON_MAP: Record<string, typeof File> = {
  dir: Folder,
  duckdb: Database,
  npy: File,
  mat: FileSpreadsheet,
  xlsx: FileSpreadsheet,
  h5: File,
  csv: Table,
};

const TYPE_LABELS: Record<string, string> = {
  duckdb: ".duckdb",
  npy: ".npy",
  mat: ".mat",
  xlsx: ".xlsx",
  h5: ".h5",
  csv: ".csv",
};

function formatSize(bytes: number | null): string {
  if (bytes == null) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface FileBrowserProps {
  open: boolean;
  onClose: () => void;
  onSelect: (paths: string[]) => void;
  multiSelect?: boolean;
}

export function FileBrowser({
  open,
  onClose,
  onSelect,
  multiSelect = true,
}: FileBrowserProps) {
  const [data, setData] = useState<BrowseResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const navigate = useCallback(async (path: string) => {
    setLoading(true);
    setError(null);
    setSelected(new Set());
    try {
      const res = await api.browse(path);
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Browse failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) navigate("~");
  }, [open, navigate]);

  if (!open) return null;

  const visibleEntries = (data?.entries ?? []).filter(
    (e) => e.type === "dir" || e.type !== "file",
  );

  const toggleSelect = (path: string, e: React.MouseEvent) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (multiSelect && (e.ctrlKey || e.metaKey)) {
        if (next.has(path)) next.delete(path);
        else next.add(path);
      } else {
        if (next.has(path) && next.size === 1) next.clear();
        else {
          next.clear();
          next.add(path);
        }
      }
      return next;
    });
  };

  const handleDoubleClick = (entry: BrowseEntry) => {
    if (entry.type === "dir") navigate(entry.path);
  };

  const handleConfirm = () => {
    if (selected.size > 0) {
      onSelect(Array.from(selected));
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-panel border border-theme-border rounded-lg shadow-xl w-full max-w-lg flex flex-col max-h-[80vh]">
        {/* Header */}
        <div className="flex items-center gap-2 px-3 py-2 border-b border-theme-border">
          <span className="text-xs font-semibold text-theme-text flex-1 truncate">
            {data?.current ?? "Loading..."}
          </span>
          <button
            onClick={onClose}
            className="text-theme-text/50 hover:text-theme-text"
          >
            <X size={16} />
          </button>
        </div>

        {/* Navigation bar */}
        <div className="flex items-center gap-1 px-3 py-1.5 border-b border-theme-border">
          <button
            onClick={() => data?.parent && navigate(data.parent)}
            disabled={!data?.parent}
            className="btn-sm bg-panel border border-theme-border text-accent disabled:opacity-30"
            title="Go up"
          >
            <ArrowUp size={14} />
          </button>
          <span className="text-xs text-theme-text/50 truncate flex-1">
            {data?.current ?? ""}
          </span>
        </div>

        {/* Entry list */}
        <div className="flex-1 overflow-y-auto min-h-0 px-1 py-1">
          {loading && (
            <p className="text-xs text-theme-text/50 p-3 text-center">
              Loading...
            </p>
          )}
          {error && (
            <p className="text-xs text-red-400 p-3 text-center">{error}</p>
          )}
          {!loading && !error && visibleEntries.length === 0 && (
            <p className="text-xs text-theme-text/50 p-3 text-center">
              Empty directory
            </p>
          )}
          {!loading &&
            visibleEntries.map((entry) => {
              const Icon = ICON_MAP[entry.type] ?? File;
              const isSelected = selected.has(entry.path);
              return (
                <div
                  key={entry.path}
                  onClick={(e) => toggleSelect(entry.path, e)}
                  onDoubleClick={() => handleDoubleClick(entry)}
                  className={`flex items-center gap-2 px-2 py-1 rounded cursor-pointer text-xs ${
                    isSelected
                      ? "bg-accent/20 text-accent"
                      : "hover:bg-white/5 text-theme-text/80"
                  }`}
                >
                  <Icon
                    size={14}
                    className={
                      entry.type === "dir" ? "text-accent/70" : "text-theme-text/40"
                    }
                  />
                  <span className="flex-1 truncate">{entry.name}</span>
                  {entry.type !== "dir" && (
                    <span className="text-theme-text/30 whitespace-nowrap">
                      {TYPE_LABELS[entry.type] ?? ""}{" "}
                      {formatSize(entry.size)}
                    </span>
                  )}
                </div>
              );
            })}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-3 py-2 border-t border-theme-border">
          <span className="text-xs text-theme-text/40">
            {selected.size > 0
              ? `${selected.size} selected`
              : multiSelect
                ? "Click to select, Ctrl+click for multiple"
                : "Click to select"}
          </span>
          <div className="flex gap-1">
            <button
              onClick={onClose}
              className="btn-sm bg-panel border border-theme-border text-theme-text/70"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={selected.size === 0}
              className="btn-sm bg-accent text-accent-contrast font-semibold disabled:opacity-50"
            >
              Select
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
