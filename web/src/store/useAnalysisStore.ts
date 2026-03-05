import { create } from "zustand";

interface AnalysisStore {
  eventLabel: string;
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

  setEventLabel: (v: string) => void;
  setViewLevel: (v: string) => void;
  setPreEventS: (v: number) => void;
  setPostEventS: (v: number) => void;
  setEnableDfof: (v: boolean) => void;
  setDfofPercentile: (v: number) => void;
  setEnableZscore: (v: boolean) => void;
  setEnableSmooth: (v: boolean) => void;
  setSmoothingSigma: (v: number) => void;
  setBufferMs: (v: number) => void;
  setMinTrials: (v: number) => void;
}

export const useAnalysisStore = create<AnalysisStore>((set) => ({
  eventLabel: "",
  viewLevel: "Population",
  preEventS: 5.0,
  postEventS: 10.0,
  enableDfof: true,
  dfofPercentile: 8.0,
  enableZscore: true,
  enableSmooth: true,
  smoothingSigma: 2.0,
  bufferMs: 0,
  minTrials: 3,

  setEventLabel: (v) => set({ eventLabel: v }),
  setViewLevel: (v) => set({ viewLevel: v }),
  setPreEventS: (v) => set({ preEventS: v }),
  setPostEventS: (v) => set({ postEventS: v }),
  setEnableDfof: (v) => set({ enableDfof: v }),
  setDfofPercentile: (v) => set({ dfofPercentile: v }),
  setEnableZscore: (v) => set({ enableZscore: v }),
  setEnableSmooth: (v) => set({ enableSmooth: v }),
  setSmoothingSigma: (v) => set({ smoothingSigma: v }),
  setBufferMs: (v) => set({ bufferMs: v }),
  setMinTrials: (v) => set({ minTrials: v }),
}));
