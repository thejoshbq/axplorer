import { create } from "zustand";

interface AnalysisStore {
  eventLabels: string[];
  viewLevel: string;
  preEventS: number;
  postEventS: number;
  enableDfof: boolean;
  dfofPercentile: number;
  enableZscore: boolean;
  enableSmooth: boolean;
  smoothingSigma: number;
  bufferMs: number;
  minTrials: number;
  enableHeatmap: boolean;
  sortMethod: string;

  setEventLabels: (v: string[]) => void;
  toggleEventLabel: (v: string) => void;
  setPreEventS: (v: number) => void;
  setPostEventS: (v: number) => void;
  setEnableDfof: (v: boolean) => void;
  setDfofPercentile: (v: number) => void;
  setEnableZscore: (v: boolean) => void;
  setEnableSmooth: (v: boolean) => void;
  setSmoothingSigma: (v: number) => void;
  setBufferMs: (v: number) => void;
  setMinTrials: (v: number) => void;
  setEnableHeatmap: (v: boolean) => void;
  setSortMethod: (v: string) => void;
}

export const useAnalysisStore = create<AnalysisStore>((set, get) => ({
  eventLabels: [],
  viewLevel: "FOV",
  preEventS: 5.0,
  postEventS: 10.0,
  enableDfof: true,
  dfofPercentile: 8.0,
  enableZscore: true,
  enableSmooth: true,
  smoothingSigma: 2.0,
  bufferMs: 0,
  minTrials: 3,
  enableHeatmap: true,
  sortMethod: "none",

  setEventLabels: (v) => set({ eventLabels: v }),
  toggleEventLabel: (v) => {
    const { eventLabels } = get();
    set({
      eventLabels: eventLabels.includes(v)
        ? eventLabels.filter((l) => l !== v)
        : [...eventLabels, v],
    });
  },
  setPreEventS: (v) => set({ preEventS: v }),
  setPostEventS: (v) => set({ postEventS: v }),
  setEnableDfof: (v) => set({ enableDfof: v }),
  setDfofPercentile: (v) => set({ dfofPercentile: v }),
  setEnableZscore: (v) => set({ enableZscore: v }),
  setEnableSmooth: (v) => set({ enableSmooth: v }),
  setSmoothingSigma: (v) => set({ smoothingSigma: v }),
  setBufferMs: (v) => set({ bufferMs: v }),
  setMinTrials: (v) => set({ minTrials: v }),
  setEnableHeatmap: (v) => set({ enableHeatmap: v }),
  setSortMethod: (v) => set({ sortMethod: v }),
}));
