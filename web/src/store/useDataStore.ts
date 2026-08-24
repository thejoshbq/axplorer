import { create } from "zustand";
import { api } from "../api/client";

interface DataStore {
  tracePath: string;
  eventPath: string;
  frameTimestampsPath: string;
  loading: boolean;
  status: string;
  availableEvents: string[];
  eventCounts: Record<string, number>;
  fovCount: number;
  populationCount: number;
  populationNames: string[];
  availableH5Kinds: string[];
  h5Kind: string | null;
  signalKind: string | null;
  lastDir: string | null;

  setTracePath: (path: string) => void;
  setEventPath: (path: string) => void;
  setFrameTimestampsPath: (path: string) => void;
  setH5Kind: (kind: string | null) => void;
  setLastDir: (path: string) => void;
  loadData: () => Promise<void>;
}

export const useDataStore = create<DataStore>((set, get) => ({
  tracePath: "",
  eventPath: "",
  frameTimestampsPath: "",
  loading: false,
  status: "No data loaded.",
  availableEvents: [],
  eventCounts: {},
  fovCount: 0,
  populationCount: 0,
  populationNames: [],
  availableH5Kinds: [],
  h5Kind: null,
  signalKind: null,
  lastDir: null,

  setTracePath: (path) => {
    set({ tracePath: path, availableH5Kinds: [], h5Kind: null });
    if (!path) return;
    // Auto-detect available trace kinds for .h5 sources in the background.
    api.detect([path]).then((res) => {
      set({ availableH5Kinds: res.available_h5_kinds });
    }).catch(() => {});
  },

  setEventPath: (path) => set({ eventPath: path }),
  setFrameTimestampsPath: (path) => set({ frameTimestampsPath: path }),
  setH5Kind: (kind) => set({ h5Kind: kind }),
  setLastDir: (path) => set({ lastDir: path }),

  loadData: async () => {
    const { tracePath, eventPath, frameTimestampsPath, h5Kind } = get();
    const paths = [tracePath, eventPath, frameTimestampsPath].filter(Boolean);
    set({ loading: true, status: "Loading..." });
    try {
      const res = await api.loadData(paths, "filesystem", "Files", undefined, h5Kind);
      set({
        loading: false,
        status: res.status,
        availableEvents: res.available_events,
        eventCounts: res.event_counts,
        fovCount: res.fov_count,
        populationCount: res.population_count,
        populationNames: res.population_names,
        signalKind: h5Kind,
      });
    } catch (err) {
      set({
        loading: false,
        status: `Error: ${err instanceof Error ? err.message : String(err)}`,
      });
    }
  },
}));
