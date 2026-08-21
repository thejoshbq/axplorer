import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-cartesian-dist-min";
import { useThemeStore } from "../../store/useThemeStore";
import { useAnalysisStore } from "../../store/useAnalysisStore";
import type { HeatmapData } from "../../api/client";

const Plot = createPlotlyComponent(Plotly);

interface Props {
  heatmap: HeatmapData;
  time: number[];
  zRange: [number, number];
}

const SEQUENTIAL_SCALE: [number, string][] = [
  [0, "rgb(0,0,0)"],
  [0.25, "rgb(0,50,70)"],
  [0.5, "rgb(0,110,130)"],
  [0.75, "rgb(0,175,195)"],
  [1, "rgb(0,229,255)"],
];

const DIVERGING_SCALE: [number, string][] = [
  [0, "rgb(255,0,200)"],
  [0.25, "rgb(140,0,110)"],
  [0.5, "rgb(0,0,0)"],
  [0.75, "rgb(0,120,140)"],
  [1, "rgb(0,229,255)"],
];

export function HeatmapChart({ heatmap, time, zRange }: Props) {
  const mode = useThemeStore((s) => s.mode);
  const enableZscore = useAnalysisStore((s) => s.enableZscore);
  const isDark = mode === "dark";

  const paperBg = isDark ? "rgb(14,18,20)" : "rgb(250,253,253)";
  const fontColor = isDark ? "rgb(210,245,245)" : "rgb(10,20,20)";
  const gridColor = isDark ? "rgb(30,40,45)" : "rgb(220,230,230)";
  const vlineColor = isDark ? "white" : "black";

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
            title: { text: enableZscore ? "Z-score" : "Activity", side: "right" as const, font: { color: fontColor, size: 10 } },
            tickfont: { color: fontColor, size: 9 },
            outlinecolor: gridColor,
          },
        },
      ]}
      layout={{
        paper_bgcolor: paperBg,
        plot_bgcolor: paperBg,
        font: {
          color: fontColor,
          family: "JetBrains Mono, monospace",
          size: 11,
        },
        xaxis: {
          title: { text: "Time (s)" },
          gridcolor: gridColor,
          linecolor: "rgba(0,212,216,0.3)",
          zerolinecolor: gridColor,
        },
        yaxis: {
          gridcolor: gridColor,
          linecolor: "rgba(0,212,216,0.3)",
          autorange: "reversed" as const,
        },
        shapes: [
          {
            type: "line",
            x0: 0,
            x1: 0,
            y0: -0.5,
            y1: heatmap.n_neurons - 0.5,
            line: { dash: "dash", color: vlineColor, width: 0.8 },
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
