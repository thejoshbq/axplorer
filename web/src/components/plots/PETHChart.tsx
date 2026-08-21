import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-cartesian-dist-min";
import { useThemeStore } from "../../store/useThemeStore";

const Plot = createPlotlyComponent(Plotly);

const COLOR_PALETTE = [
  "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
  "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52",
];

function hexToRgba(hex: string, alpha: number): string {
  const h = hex.replace("#", "");
  const r = parseInt(h.substring(0, 2), 16);
  const g = parseInt(h.substring(2, 4), 16);
  const b = parseInt(h.substring(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

interface Props {
  title: string;
  time: number[];
  mean: number[];
  median: number[];
  sem: number[];
  yRange: [number, number];
  colorIndex: number;
}

export function PETHChart({ title, time, mean, median, sem, yRange, colorIndex }: Props) {
  const mode = useThemeStore((s) => s.mode);
  const isDark = mode === "dark";
  const color = COLOR_PALETTE[colorIndex % COLOR_PALETTE.length];

  const paperBg = isDark ? "rgb(14,18,20)" : "rgb(250,253,253)";
  const fontColor = isDark ? "rgb(210,245,245)" : "rgb(10,20,20)";
  const gridColor = isDark ? "rgb(30,40,45)" : "rgb(220,230,230)";
  const vlineColor = isDark ? "white" : "black";

  const upperBound = mean.map((m, i) => m + sem[i]);
  const lowerBound = mean.map((m, i) => m - sem[i]);

  return (
    <Plot
      data={[
        {
          x: [...time, ...[...time].reverse()],
          y: [...upperBound, ...[...lowerBound].reverse()],
          fill: "toself",
          fillcolor: hexToRgba(color, 0.2),
          line: { width: 0 },
          hoverinfo: "skip" as const,
          showlegend: false,
          type: "scatter" as const,
        },
        {
          x: time,
          y: mean,
          mode: "lines" as const,
          line: { color, width: 1.5 },
          name: "Mean",
          hovertemplate: "Time: %{x:.3f}s<br>Mean: %{y:.4f}<extra></extra>",
          showlegend: true,
          type: "scatter" as const,
        },
        {
          x: time,
          y: median,
          mode: "lines" as const,
          line: { color, width: 1.5, dash: "dot" },
          name: "Median",
          hovertemplate: "Time: %{x:.3f}s<br>Median: %{y:.4f}<extra></extra>",
          showlegend: true,
          type: "scatter" as const,
        },
      ]}
      layout={{
        title: { text: title, font: { size: 12 } },
        paper_bgcolor: paperBg,
        plot_bgcolor: paperBg,
        font: { color: fontColor, family: "JetBrains Mono, monospace", size: 11 },
        xaxis: {
          title: { text: "Time (s)" },
          gridcolor: gridColor,
          linecolor: `rgba(0,212,216,0.3)`,
          zerolinecolor: gridColor,
        },
        yaxis: {
          title: { text: "Population Activity" },
          range: yRange,
          gridcolor: gridColor,
          linecolor: `rgba(0,212,216,0.3)`,
          zerolinecolor: gridColor,
        },
        legend: {
          orientation: "h",
          x: 0, y: 1.12,
          font: { size: 9 },
        },
        shapes: [
          {
            type: "line",
            x0: 0, x1: 0,
            y0: yRange[0], y1: yRange[1],
            line: { dash: "dash", color: vlineColor, width: 0.8 },
            opacity: 0.6,
          },
        ],
        margin: { l: 55, r: 20, t: 40, b: 40 },
        autosize: true,
      }}
      useResizeHandler
      style={{ width: "100%", height: "350px" }}
      config={{ responsive: true, displayModeBar: false }}
    />
  );
}
