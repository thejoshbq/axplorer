import { create } from "zustand";
import { api, type HeatmapData } from "../api/client";
import { useAnalysisStore } from "./useAnalysisStore";

interface PlotData {
  title: string;
  time: number[];
  mean: number[];
  median: number[];
  sem: number[];
  heatmap?: HeatmapData;
}

interface PlotStore {
  plots: PlotData[];
  yRange: [number, number];
  zRange: [number, number];
  eventLabels: string[];
  dfofSkippedReason: string | null;
  computing: boolean;
  error: string | null;

  compute: () => Promise<void>;
  clear: () => void;
}

export const usePlotStore = create<PlotStore>((set) => ({
  plots: [],
  yRange: [0, 1],
  zRange: [0, 1],
  eventLabels: [],
  dfofSkippedReason: null,
  computing: false,
  error: null,

  compute: async () => {
    const a = useAnalysisStore.getState();
    set({ computing: true, error: null });
    try {
      const res = await api.compute({
        event_labels: a.eventLabels,
        view_level: a.viewLevel,
        pre_event_s: a.preEventS,
        post_event_s: a.postEventS,
        enable_dfof: a.enableDfof,
        dfof_percentile: a.dfofPercentile,
        enable_zscore: a.enableZscore,
        enable_smooth: a.enableSmooth,
        smoothing_sigma: a.smoothingSigma,
        buffer_ms: a.bufferMs,
        min_trials: a.minTrials,
        enable_heatmap: a.enableHeatmap,
        sort_method: a.sortMethod,
      });
      set({
        computing: false,
        plots: res.plots,
        yRange: res.y_range as [number, number],
        zRange: res.z_range as [number, number],
        eventLabels: res.event_labels,
        dfofSkippedReason: res.dfof_skipped_reason,
      });
    } catch (err) {
      set({
        computing: false,
        error: err instanceof Error ? err.message : String(err),
      });
    }
  },

  clear: () =>
    set({ plots: [], yRange: [0, 1], zRange: [0, 1], eventLabels: [], dfofSkippedReason: null, error: null }),
}));
