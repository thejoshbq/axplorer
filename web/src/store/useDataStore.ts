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

  setSource: (source: "filesystem" | "database") => void;
  setDbPath: (path: string) => void;
  setDataLevel: (level: string) => void;
  addPath: (path: string) => void;
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

  setSource: (source) => set({ source }),
  setDbPath: (path) => set({ dbPath: path }),
  setDataLevel: (level) => set({ dataLevel: level }),

  addPath: (path) =>
    set((s) => {
      if (s.paths.includes(path)) return s;
      return { paths: [...s.paths, path] };
    }),

  removePath: (path) =>
    set((s) => ({ paths: s.paths.filter((p) => p !== path) })),

  loadData: async () => {
    const { source, dbPath, dataLevel, paths } = get();
    set({ loading: true, status: "Loading..." });
    try {
      const res = await api.loadData(
        source,
        dataLevel,
        paths,
        dbPath || undefined,
      );
      set({
        loading: false,
        status: res.status,
        availableEvents: res.available_events,
        fovCount: res.fov_count,
        populationCount: res.population_count,
      });
    } catch (err) {
      set({
        loading: false,
        status: `Error: ${err instanceof Error ? err.message : String(err)}`,
      });
    }
  },
}));
