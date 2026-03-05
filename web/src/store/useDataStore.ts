import { create } from "zustand";
import { api } from "../api/client";

interface DataStore {
  dataLevel: string;
  paths: string[];
  loading: boolean;
  status: string;
  availableEvents: string[];
  fovCount: number;
  populationCount: number;

  setDataLevel: (level: string) => void;
  addPath: (path: string) => void;
  removePath: (path: string) => void;
  loadData: () => Promise<void>;
}

export const useDataStore = create<DataStore>((set, get) => ({
  dataLevel: "Project",
  paths: [],
  loading: false,
  status: "No data loaded.",
  availableEvents: [],
  fovCount: 0,
  populationCount: 0,

  setDataLevel: (level) => set({ dataLevel: level }),

  addPath: (path) =>
    set((s) => {
      if (s.paths.includes(path)) return s;
      return { paths: [...s.paths, path] };
    }),

  removePath: (path) =>
    set((s) => ({ paths: s.paths.filter((p) => p !== path) })),

  loadData: async () => {
    const { dataLevel, paths } = get();
    set({ loading: true, status: "Loading..." });
    try {
      const res = await api.loadData(dataLevel, paths);
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
