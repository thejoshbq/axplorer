import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-cartesian-dist-min";
import { plotly, color } from "@phoxel/tokens";

const Plot = createPlotlyComponent(Plotly);

const baseLayout = plotly.layout as any;
const COLOR_PALETTE = baseLayout.colorway as string[];

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
  const seriesColor = COLOR_PALETTE[colorIndex % COLOR_PALETTE.length];

  const upperBound = mean.map((m, i) => m + sem[i]);
  const lowerBound = mean.map((m, i) => m - sem[i]);

  return (
    <Plot
      data={[
        {
          x: [...time, ...[...time].reverse()],
          y: [...upperBound, ...[...lowerBound].reverse()],
          fill: "toself",
          fillcolor: hexToRgba(seriesColor, 0.2),
          line: { width: 0 },
          hoverinfo: "skip" as const,
          showlegend: false,
          type: "scatter" as const,
        },
        {
          x: time,
          y: mean,
          mode: "lines" as const,
          line: { color: seriesColor, width: 1.5 },
          name: "Mean",
          hovertemplate: "Time: %{x:.3f}s<br>Mean: %{y:.4f}<extra></extra>",
          showlegend: true,
          type: "scatter" as const,
        },
        {
          x: time,
          y: median,
          mode: "lines" as const,
          line: { color: seriesColor, width: 1.5, dash: "dot" },
          name: "Median",
          hovertemplate: "Time: %{x:.3f}s<br>Median: %{y:.4f}<extra></extra>",
          showlegend: true,
          type: "scatter" as const,
        },
      ]}
      layout={{
        ...baseLayout,
        title: { text: title, font: { size: 12 } },
        xaxis: {
          ...baseLayout.xaxis,
          title: { text: "Time (s)" },
        },
        yaxis: {
          ...baseLayout.yaxis,
          title: { text: "Population Activity" },
          range: yRange,
        },
        legend: {
          ...baseLayout.legend,
          orientation: "h",
          x: 0, y: 1.12,
          font: { ...baseLayout.legend.font, size: 9 },
        },
        shapes: [
          {
            type: "line",
            x0: 0, x1: 0,
            y0: yRange[0], y1: yRange[1],
            line: { dash: "dash", color: color["text-strong"], width: 0.8 },
            opacity: 0.6,
          },
        ],
        autosize: true,
      }}
      useResizeHandler
      style={{ width: "100%", height: "350px" }}
      config={{ responsive: true, displayModeBar: false }}
    />
  );
}
