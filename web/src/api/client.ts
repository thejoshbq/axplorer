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
}

interface PlotData {
  title: string;
  time: number[];
  mean: number[];
  sem: number[];
}

interface ComputeResponse {
  plots: PlotData[];
  y_range: number[];
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
  loadData: (dataLevel: string, paths: string[]) =>
    request<LoadResponse>("/api/load", {
      method: "POST",
      body: JSON.stringify({ data_level: dataLevel, paths }),
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
    eventLabel: string,
    fmt: string,
    dark: boolean,
  ): Promise<Blob> => {
    const res = await fetch("/api/export/figure", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plots, y_range: yRange, event_label: eventLabel, fmt, dark }),
    });
    if (!res.ok) throw new Error(`Export failed: ${res.status}`);
    return res.blob();
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
