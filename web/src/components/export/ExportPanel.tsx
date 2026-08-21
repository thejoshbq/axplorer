import { useState } from "react";
import { Download } from "lucide-react";
import { api } from "../../api/client";
import { useThemeStore } from "../../store/useThemeStore";
import { useAnalysisStore } from "../../store/useAnalysisStore";
import { usePlotStore } from "../../store/usePlotStore";

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function ExportPanel() {
  const [figureFmt, setFigureFmt] = useState("png");
  const [dataFmt, setDataFmt] = useState("csv");
  const [exporting, setExporting] = useState(false);

  const mode = useThemeStore((s) => s.mode);
  const analysis = useAnalysisStore();
  const { plots, yRange, zRange, eventLabels } = usePlotStore();

  const hasPlotsToExport = plots.length > 0;
  // The figure/data export endpoints caption on a single event label; when
  // several are selected for comparison, export the first one.
  const primaryEventLabel = analysis.eventLabels[0] ?? "";

  const handleExportFigure = async () => {
    if (!hasPlotsToExport) return;
    setExporting(true);
    try {
      const label = eventLabels[0] ?? primaryEventLabel;
      const blob = await api.exportFigure(plots, yRange, zRange, label, figureFmt, mode === "dark", analysis.enableZscore);
      downloadBlob(blob, `axplorer_peth.${figureFmt}`);
    } catch (err) {
      console.error("Figure export failed:", err);
    } finally {
      setExporting(false);
    }
  };

  const handleExportData = async () => {
    setExporting(true);
    try {
      const blob = await api.exportData({
        event_label: primaryEventLabel,
        fmt: dataFmt,
        pre_event_s: analysis.preEventS,
        post_event_s: analysis.postEventS,
        enable_dfof: analysis.enableDfof,
        dfof_percentile: analysis.dfofPercentile,
        enable_zscore: analysis.enableZscore,
        enable_smooth: analysis.enableSmooth,
        smoothing_sigma: analysis.smoothingSigma,
        buffer_ms: analysis.bufferMs,
        min_trials: analysis.minTrials,
      });
      const ext = dataFmt === "hdf5" ? "h5" : dataFmt;
      downloadBlob(blob, `axplorer_peth.${ext}`);
    } catch (err) {
      console.error("Data export failed:", err);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-3">
      {/* Figure export */}
      <div>
        <label className="block text-xs text-[rgb(var(--color-text-secondary))] mb-1">Figure Format</label>
        <div className="flex gap-2">
          <select value={figureFmt} onChange={(e) => setFigureFmt(e.target.value)} className="input-base flex-1">
            <option value="png">PNG</option>
            <option value="svg">SVG</option>
            <option value="pdf">PDF</option>
          </select>
          <button
            onClick={handleExportFigure}
            disabled={!hasPlotsToExport || exporting}
            className="btn-sm bg-panel border border-theme-border text-accent disabled:opacity-50 flex items-center gap-1"
          >
            <Download size={12} />
            Figure
          </button>
        </div>
      </div>

      {/* Data export */}
      <div>
        <label className="block text-xs text-[rgb(var(--color-text-secondary))] mb-1">Data Format</label>
        <div className="flex gap-2">
          <select value={dataFmt} onChange={(e) => setDataFmt(e.target.value)} className="input-base flex-1">
            <option value="csv">CSV</option>
            <option value="hdf5">HDF5</option>
          </select>
          <button
            onClick={handleExportData}
            disabled={!primaryEventLabel || exporting}
            className="btn-sm bg-panel border border-theme-border text-accent disabled:opacity-50 flex items-center gap-1"
          >
            <Download size={12} />
            Data
          </button>
        </div>
      </div>
    </div>
  );
}
