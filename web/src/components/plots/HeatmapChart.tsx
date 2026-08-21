import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-cartesian-dist-min";
import { useAnalysisStore } from "../../store/useAnalysisStore";
import { plotly, color } from "@phoxel/tokens";
import type { HeatmapData } from "../../api/client";

const Plot = createPlotlyComponent(Plotly);
const baseLayout = plotly.layout as any;

interface Props {
  heatmap: HeatmapData;
  time: number[];
  zRange: [number, number];
}

// No sequential/diverging colorscale token exists (only a categorical
// colorway) -- these stay bespoke, anchored to the accent/surface tokens
// where they already coincide.
const SEQUENTIAL_SCALE: [number, string][] = [
  [0, color["surface-0"]],
  [0.25, "rgb(0,50,70)"],
  [0.5, "rgb(0,110,130)"],
  [0.75, "rgb(0,175,195)"],
  [1, color.accent],
];

const DIVERGING_SCALE: [number, string][] = [
  [0, "rgb(255,0,200)"],
  [0.25, "rgb(140,0,110)"],
  [0.5, color["surface-0"]],
  [0.75, "rgb(0,120,140)"],
  [1, color.accent],
];

export function HeatmapChart({ heatmap, time, zRange }: Props) {
  const enableZscore = useAnalysisStore((s) => s.enableZscore);

  const colorscale = enableZscore ? DIVERGING_SCALE : SEQUENTIAL_SCALE;
  const height = Math.min(400, Math.max(200, heatmap.n_neurons * 5));

  return (
    <Plot
      data={[
        {
          z: heatmap.z,
          x: time,
          y: heatmap.neuron_labels,
          type: "heatmap" as const,
          colorscale,
          zmin: zRange[0],
          zmax: zRange[1],
          hovertemplate:
            "Time: %{x:.3f}s<br>%{y}<br>Value: %{z:.4f}<extra></extra>",
          colorbar: {
            title: { text: enableZscore ? "Z-score" : "Activity", side: "right" as const, font: baseLayout.font },
            tickfont: baseLayout.xaxis.tickfont,
            outlinecolor: baseLayout.xaxis.linecolor,
          },
        },
      ]}
      layout={{
        ...baseLayout,
        xaxis: {
          ...baseLayout.xaxis,
          title: { text: "Time (s)" },
        },
        yaxis: {
          ...baseLayout.yaxis,
          autorange: "reversed" as const,
        },
        shapes: [
          {
            type: "line",
            x0: 0,
            x1: 0,
            y0: -0.5,
            y1: heatmap.n_neurons - 0.5,
            line: { dash: "dash", color: color["text-strong"], width: 0.8 },
            opacity: 0.6,
          },
        ],
        margin: { l: 70, r: 20, t: 10, b: 40 },
        autosize: true,
      }}
      useResizeHandler
      style={{ width: "100%", height: `${height}px` }}
      config={{ responsive: true, displayModeBar: false }}
    />
  );
}
