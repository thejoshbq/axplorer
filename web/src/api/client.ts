interface LoadResponse {
  status: string;
  available_events: string[];
  fov_count: number;
  population_count: number;
}

interface ComputeRequest {
  event_label: string;
  view_level: string;
  pre_event_s: number;
  post_event_s: number;
  enable_dfof: boolean;
  dfof_percentile: number;
  enable_zscore: boolean;
  enable_smooth: boolean;
  smoothing_sigma: number;
  buffer_ms: number;
  min_trials: number;
  enable_heatmap: boolean;
  sort_method: string;
}

export interface HeatmapData {
  z: number[][];
  neuron_labels: string[];
  n_neurons: number;
  sort_method: string;
}

interface PlotData {
  title: string;
  time: number[];
  mean: number[];
  sem: number[];
  heatmap?: HeatmapData;
}

interface ComputeResponse {
  plots: PlotData[];
  y_range: number[];
  z_range: number[];
  event_label: string;
}

interface StatusResponse {
  status: string;
  loading: boolean;
  available_events: string[];
  fov_count: number;
  population_count: number;
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  loadData: (
    source: string,
    dataLevel: string,
    paths: string[],
    dbPath?: string,
  ) =>
    request<LoadResponse>("/api/load", {
      method: "POST",
      body: JSON.stringify({
        source,
        data_level: dataLevel,
        paths,
        db_path: dbPath ?? null,
      }),
    }),

  getStatus: () => request<StatusResponse>("/api/status"),

  compute: (params: ComputeRequest) =>
    request<ComputeResponse>("/api/compute", {
      method: "POST",
      body: JSON.stringify(params),
    }),

  exportFigure: async (
    plots: PlotData[],
    yRange: number[],
    zRange: number[],
    eventLabel: string,
    fmt: string,
    dark: boolean,
  ): Promise<Blob> => {
    const res = await fetch("/api/export/figure", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plots, y_range: yRange, z_range: zRange, event_label: eventLabel, fmt, dark }),
    });
    if (!res.ok) throw new Error(`Export failed: ${res.status}`);
    return res.blob();
  },

  uploadDbFile: async (file: File): Promise<{ db_path: string }> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch("/api/db/upload", { method: "POST", body: form });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json();
  },

  exportData: async (params: {
    event_label: string;
    fmt: string;
    pre_event_s: number;
    post_event_s: number;
    enable_dfof: boolean;
    dfof_percentile: number;
    enable_zscore: boolean;
    enable_smooth: boolean;
    smoothing_sigma: number;
    buffer_ms: number;
    min_trials: number;
  }): Promise<Blob> => {
    const res = await fetch("/api/export/data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error(`Export failed: ${res.status}`);
    return res.blob();
  },
};
