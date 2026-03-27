import { create } from "zustand";
import { api } from "../api/client";

interface DataStore {
  source: "filesystem" | "database";
  dbPath: string;
  dataLevel: string;
  paths: string[];
  loading: boolean;
  status: string;
  availableEvents: string[];
  fovCount: number;
  populationCount: number;
  populationNames: string[];
  detectedSource: string | null;
  detectedLevel: string | null;

  setSource: (source: "filesystem" | "database") => void;
  setDbPath: (path: string) => void;
  setDataLevel: (level: string) => void;
  addPath: (path: string) => void;
  addPaths: (paths: string[]) => void;
  removePath: (path: string) => void;
  loadData: () => Promise<void>;
}

export const useDataStore = create<DataStore>((set, get) => ({
  source: "filesystem",
  dbPath: "",
  dataLevel: "Project",
  paths: [],
  loading: false,
  status: "No data loaded.",
  availableEvents: [],
  fovCount: 0,
  populationCount: 0,
  populationNames: [],
  detectedSource: null,
  detectedLevel: null,

  setSource: (source) => set({ source }),
  setDbPath: (path) => set({ dbPath: path }),
  setDataLevel: (level) => set({ dataLevel: level }),

  addPath: (path) => {
    const s = get();
    if (s.paths.includes(path)) return;
    const newPaths = [...s.paths, path];
    set({ paths: newPaths });
    // Auto-detect in background.
    api.detect(newPaths).then((res) => {
      set({
        detectedSource: res.source,
        detectedLevel: res.data_level,
        source: res.source as "filesystem" | "database",
        dataLevel: res.data_level,
      });
    }).catch(() => {});
  },

  addPaths: (paths) => {
    const s = get();
    const unique = paths.filter((p) => !s.paths.includes(p));
    if (unique.length === 0) return;
    const newPaths = [...s.paths, ...unique];
    set({ paths: newPaths });
    api.detect(newPaths).then((res) => {
      set({
        detectedSource: res.source,
        detectedLevel: res.data_level,
        source: res.source as "filesystem" | "database",
        dataLevel: res.data_level,
      });
    }).catch(() => {});
  },

  removePath: (path) =>
    set((s) => {
      const paths = s.paths.filter((p) => p !== path);
      if (paths.length === 0) {
        return { paths, detectedSource: null, detectedLevel: null };
      }
      return { paths };
    }),

  loadData: async () => {
    const { source, dbPath, dataLevel, paths } = get();
    set({ loading: true, status: "Loading..." });
    try {
      const res = await api.loadData(
        paths,
        source,
        dataLevel,
        dbPath || undefined,
      );
      set({
        loading: false,
        status: res.status,
        availableEvents: res.available_events,
        fovCount: res.fov_count,
        populationCount: res.population_count,
        populationNames: res.population_names,
      });
    } catch (err) {
      set({
        loading: false,
        status: `Error: ${err instanceof Error ? err.message : String(err)}`,
      });
    }
  },
}));
