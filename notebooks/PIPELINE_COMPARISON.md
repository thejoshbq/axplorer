# Algorithm Comparison: `reacher_analysis.ipynb` vs `Population - PFC Self-Admin 2024.04 v20_REC_notracking_forestclusteringedit.ipynb`

> **Audience.** Researchers and reviewers who know the science but want a precise, code-grounded account of how the two pipelines differ — and where each is mathematically suspect.
>
> **Method.** Both notebooks were read end-to-end. Findings are cited by cell index so the reader can navigate back. Where two implementations of the same conceptual step diverge numerically, the divergence is named explicitly and the mathematical consequence is stated.
>
> **Files compared.**
> - `reacher_analysis.ipynb` (referred to below as **REACHER**)
> - `Population - PFC Self-Admin 2024.04 v20_REC_notracking_forestclusteringedit.ipynb` (referred to as **PFC**)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Pipeline-at-a-Glance](#2-pipeline-at-a-glance)
3. [Stage-by-Stage Algorithmic Comparison](#3-stage-by-stage-algorithmic-comparison)
4. [Mathematical Significance of Each Divergence](#4-mathematical-significance-of-each-divergence)
5. [Identified Flaws & Methodological Hazards](#5-identified-flaws--methodological-hazards)
6. [Reproducibility & Determinism](#6-reproducibility--determinism)
7. [Recommendations](#7-recommendations)
8. [Appendix A — Hardcoded Constants](#appendix-a--hardcoded-constants)
9. [Appendix B — Cell Index Cross-Reference](#appendix-b--cell-index-cross-reference)

---

## 1. Executive Summary

**Scope.** This document compares the two pipelines only as far as they overlap conceptually: from raw signal ingestion through trace normalization, peri-event window extraction, per-trial baseline handling, per-neuron averaging, and population mean/SEM visualization. PFC continues past that boundary into single-neuron response classification (auROC + Mann-Whitney + BH-FDR), spectral and Random-Forest clustering, and per-cluster downstream analyses; REACHER does none of those. Those PFC-only stages are out of scope here — there is no comparison to make when only one pipeline performs the step.

The two notebooks share an acquisition model (30 Hz raw, 4× frame averaging → 7.5 Hz effective) and a peri-event analysis frame, but they are **not interchangeable** within the shared scope.

- **REACHER** is a clean, function-encapsulated, *visualization-only* pipeline. It mirrors the production `axplorer` web app's preprocessing (percentile-based ΔF/F → pre-event z-score → Gaussian smoothing) and produces three view-level PETHs / heatmaps / single-cell rasters. Outputs are in-memory only.
- **PFC** is a legacy lab notebook that performs the same preprocessing differently (F/⟨F⟩ ratio + per-trial baseline subtraction + full-session z-score) and produces a single grand-mean population trace. Its inferential and clustering stages run *after* this point and are out of scope.

Within the shared scope, the divergences that change downstream numbers — not just style — are concentrated at two points:

| # | Divergence | Direction of bias |
|---|------------|-------------------|
| D1 | **Trace normalization.** REACHER does ΔF/F with an 8th-percentile baseline; PFC divides by the session **mean** (not subtraction). | PFC systematically *under-estimates* response magnitude for high-firing neurons. Cross-pipeline magnitudes are not directly comparable. |
| D2 | **Z-score baseline scope.** REACHER uses a tight pre-event window `[-3000, -500] ms`; PFC z-scores against the **full session**. | REACHER is sensitive to anticipatory baseline contamination; PFC conflates rest and task. |

A bug also exists in REACHER's z-scorer: the 3-D-tensor code path quietly uses the entire window as baseline rather than the pre-event slice. Detail follows.

---

## 2. Pipeline-at-a-Glance

| Aspect | REACHER (`reacher_analysis.ipynb`) | PFC (`...forestclusteringedit.ipynb`) |
|---|---|---|
| Lineage | New, axplorer-equivalent pure-Python port | Legacy lab notebook (.mat + .npy ingestion) |
| Lines / cells | 18 code cells, function-encapsulated | 161 cells, mostly script-style |
| Acquisition rate | 30 Hz → 4× average → 7.5 Hz effective | Same |
| Event source | REACHER `.xlsx` (`Behavior Data` + `Frame Timestamps`) | MATLAB `eventlog` in `.mat` |
| Multi-part sessions | Not supported | Supported (concatenates `part1`–`part4`) |
| Trace normalization | ΔF/F, percentile baseline (8th) | F / mean(F) (session mean), then per-trial baseline subtraction |
| Z-score | Pre-event `[-3000, -500] ms` (2-D path) | Full session per neuron |
| Smoothing | Gaussian σ = 2 frames | None |
| Window | pre = 5 s, post = 10 s (configurable) | pre ≈ 10 s, post ≈ 11.6 s (asymmetric) |
| Buffer / event de-dup | `BUFFER_MS = 0` (off by default) | `separation_requirement = 1000 ms` (always on) |
| Trial cap | None | `activeleverall[:300]` (silent, asymmetric) |
| Min trials | 3 | 3 |
| Per-trial baseline subtraction | None (z-score plays this role) | Mean of frames 0:22 (= first 3 s of pre-event window) |
| Population view | FOV / Sample / Population (axplorer's three levels) | Single grand mean across neurons |
| Neuron ordering for heatmap | Sort by argmax / argmin / abs-peak | Grouped by cluster (cluster step out of scope) |
| Downstream stages (out of scope) | n/a | Single-neuron auROC + Mann-Whitney + FDR, RF cluster transfer, per-cluster heatmaps, stability tests |

---

## 3. Stage-by-Stage Algorithmic Comparison

### 3.1 Data ingestion and event encoding

**REACHER** (cells 5–8) reads two artifacts per FOV:
- `*extractedsignals_raw.npy` — `(neurons, frames)`
- a single `.xlsx` with sheets `Behavior Data` and `Frame Timestamps`

The `REACHER_EVENT_DICT` (cell 2) maps integer codes (101–702) to human-readable labels (`rh_lever_active_press`, `pump_infusion`, `cue_tone_on`, `lick_on`, `pavlovian_trial_start`, etc.).

```python
# cell 7, load_fov_directory — frame-timestamp tolerance
if abs(len(ts) - num_frames) > max(8, num_frames * 0.005):
    # silent fallback to synthetic regular grid (no warning)
```

**PFC** (cell 2, `analyze_single_session`) reads `.npy` signals and a MATLAB `.mat` with an `eventlog` two-column array (`[code, timestamp_ms]`). Codes are numeric only:

| Code | Meaning |
|------|---------|
| 22 | active lever |
| 222 | active lever during timeout |
| 21 | inactive lever |
| 212 | inactive lever during timeout |
| 7 | cues |
| 4 | infusions |
| 9 | frame timestamps |

Two structural differences:

1. **Multi-part concatenation.** PFC supports up to 4 split recording files (`part1`–`part4`); each part's eventlog is offset by the previous part's last frame timestamp before being stacked (cell 2). REACHER has no equivalent.
2. **Aliased channels.** PFC defines `activeleverall = sort(activelever ∪ activelevertimeout)` and applies a hard cap of `[:300]` (cell 2). REACHER never aliases events.

### 3.2 Multi-part / split-session handling

PFC concatenates signals via `np.hstack` and adds the running max-timestamp offset to each subsequent eventlog. There is no validation that the gap between parts is consistent with the frame rate, so *if a session is split mid-recording with a non-trivial gap, that gap is silently elided.* REACHER does not face this because its data model is one Sample = one signal file.

### 3.3 Event de-duplication

| | REACHER | PFC |
|---|---|---|
| Default | `BUFFER_MS = 0` (off) | `delete_overlaps = 'yes'`, `separation_requirement = 1000 ms` |
| Mechanism | If on, drops the *later* of any pair within buffer | `np.delete(temp, np.argwhere(np.ediff1d(temp) < 1000) + 1)` — drops the *later* of any pair within 1 s |
| Configurable per analysis | Yes (slider) | Module-level only |

PFC always discards rapid-fire pairs (e.g. lever bursts within 1 s). The threshold is unmotivated in the code — there is no comment explaining why 1 s. Trial counts therefore differ from REACHER's even on identical raw data.

### 3.4 Trace-level normalization (the most important divergence)

**REACHER** (cell 10, `DFOverF`):
```python
F0 = np.percentile(signals, self.percentile, axis=-1, keepdims=True)
F0_safe = np.where(F0 == 0, np.nan, F0)
return ((signals - F0_safe) / F0_safe).astype(np.float32)
```
This is canonical ΔF/F with `F0` = the 8th percentile per neuron. The result is centered at 0; large positive excursions are events; small negative values are below-baseline.

**PFC** (cell 2):
```python
signals /= np.nanmean(signals, axis=1)[:, None]
```
This is **F / ⟨F⟩** — no subtraction. The result is centered at **1.0**, not 0. Subsequent per-trial baseline subtraction (cell 6) gives:
```
result = (F − F̄_pre) / ⟨F_session⟩
```
That is dimensionally similar to ΔF/F but with two structural changes:

1. The denominator is the **arithmetic mean** of the entire session, not a low-percentile floor.
2. The minuend is a *trial-specific* pre-event mean of frames 0:22 (i.e. −10 s … −7 s relative to event), not the global F0.

**Consequence.** For a heavily-driven neuron the session mean is inflated by the firing periods themselves, so the divisor is too large → response amplitude is *under-estimated* relative to REACHER's percentile-baseline ΔF/F. For a quiet neuron with rare transients, the two pipelines agree to within a small additive offset.

### 3.5 Z-scoring

**REACHER** (cell 10, `ZScore`) supports two modes:
- `full_trace=False` (default) — pre-event window in ms relative to onset, default `[-3000, -500] ms`.
- `full_trace=True` — full-session per-neuron z-score.

The 2-D path implements the pre-event window correctly. **The 3-D path (windows already extracted) does not:**
```python
# cell 10
if signals.ndim == 2:
    start = max(0, int(self.window_ms[0] / self.frame_duration_ms))
    end = min(int(self.window_ms[1] / self.frame_duration_ms), signals.shape[-1])
    baseline = signals[:, start:end]
else:
    # For 3-D windows the time axis is centered on the event;
    # absolute frame indices map: 0 = event onset.
    start, end = 0, signals.shape[-1]   # ← entire window!
    baseline = signals[..., start:end]
```
The comment claims `0 = event onset`, but `start = 0` is in fact the *first* frame of the window (= `−pre_s`). The result is that **the entire window — pre + post — is used as the baseline distribution.** Post-event activity contaminates the standardization. Whether this affects the canonical pipeline depends on call site, but the silent comment-vs-behavior mismatch is a real bug.

**PFC** (cell 2):
```python
if z_score_data == 'yes':
    for n in range(signals.shape[0]):
        signals[n] = (signals[n] - np.nanmean(signals[n])) / np.nanstd(signals[n])
```
Per-neuron, full session. Robust to per-trial baseline shifts but conflates inter-trial intervals with task epochs. If trials are dense the mean and std are pushed toward task-driven values, compressing apparent z-scores.

### 3.6 Trial windowing and frame alignment

**REACHER** (cell 11, `extract_event_windows`):
- Time axis: `np.linspace(-pre_s, post_s, n, endpoint=False)` with `n = round((pre_s + post_s) · fps_eff)`.
- Frame index: `idx = np.searchsorted(frame_ts_ms, t1, side="right") - 1` (clipped).
- Slice: `signals[:, idx − pre_frames : idx + post_frames]`.
- Drops any window with `start < 0` or `end > num_frames`; treats `idx == 0` as a "pre-first-frame" sentinel and skips it.

**PFC** (cell 2, with helper `framenumberforevent`):
- `pre_window_size = int(10 · 7.5) = 75 frames`.
- `window_size = int((pre_window_size · 2) + (1.6 · 7.5)) = 162 frames` (≈ 21.6 s, *not* 23.6 s as one summary stated).
- `post_window_size = window_size − pre_window_size = 87 frames` (≈ 11.6 s).
- Frame index: `np.nonzero(frame_timestamps <= e)[0][-1]`, equivalent to `searchsorted(..., side='right') - 1`.

The alignment math is the same. The *windows* differ: REACHER defaults to 5 s pre / 10 s post; PFC uses 10 s pre / 11.6 s post.

### 3.7 Tensor shape and missing-trial handling

| | REACHER | PFC |
|---|---|---|
| Output shape | `(trials, neurons, time)` | `(neurons, time, trials)` → swapped to `(neurons, trials, time)` |
| Missing trials | Dropped (window out of bounds) | `np.delete(alignedevents, i, axis=0)` |
| Per-neuron trial count | Equal across neurons within a sample | **Variable** — neurons with bad trials lose them; later `np.nanmean` hides this |

PFC's shape-then-swap pattern is a stylistic vestige; the variable-per-neuron trial count is a real concern because per-neuron means are computed with different denominators that aren't reported.

### 3.8 Per-trial baseline subtraction

PFC (cell 6) subtracts a per-trial pre-event baseline from each window before any downstream averaging. This subtracted tensor (`alignedevents`) is what feeds the population mean; the same tensor also feeds the out-of-scope auROC step.

```python
baseline = np.mean(temp2[:, baselinefirstframe:baselinelastframe, :], axis=1)
alignedevents = temp2 - baseline[:, None, :]
```

with `baselinefirstframe = 0`, `baselinelastframe = int(3 · 7.5) = 22`, i.e. frames 0..22 = first 3 s of the window = `[−10 s, −7 s]` relative to event.

This is fixed and *not adaptive*. If two events are spaced less than 7 s apart, the "baseline" of trial *n+1* overlaps the response of trial *n*, and the bias propagates into the per-neuron and population traces. The 1-second `separation_requirement` does not help because it only de-duplicates within 1 s, not within 7 s.

REACHER does not subtract a per-trial baseline; the z-score's pre-event window `[-3000, -500] ms` plays that role. The two approaches answer slightly different questions: REACHER's z-score normalizes amplitude into σ-units against pre-event variability; PFC's subtraction yields a fluorescence-ratio change relative to the trial's own baseline epoch.

### 3.9 Population aggregation

**REACHER** (cell 13, `compute_for_view`) — three view levels:
- **FOV:** one plot per Sample (one signal file).
- **Sample:** one plot per group (multiple FOVs in a folder), neurons concatenated.
- **Population:** one plot pooling all groups.

The population SEM is computed as `np.nanmean(sem_matrix, axis=0)` — i.e. the **mean of per-sample SEMs**, not the SEM of the pooled neuron-by-time matrix. This *under-states* variance and matches the axplorer implementation (the comment explicitly admits it). A pooled SEM should be `std_n_pool / sqrt(N_pool)`.

**PFC** (cell 8 onward) computes a single grand-mean across the included neurons. (The eventual subsetting by auROC sign and significance happens further downstream and is out of scope.)

### 3.10 Neuron ordering for visualization

**REACHER** sorts only (cell 12, `sort_neuron_matrix`):
- `excitatory`: ascending by `argmax` over post-event epoch.
- `inhibitory`: ascending by `argmin`.
- `magnitude`: descending by absolute peak.
- `none`: identity.

This is presentational, not analytical — it does not produce groups.

**PFC** orders the population heatmap by cluster identity, but the cluster step (spectral or RF-transfer) lives downstream of this comparison's scope. Within scope, PFC has no equivalent sorting facility on the unclustered population.

### 3.11 Visualization

| | REACHER | PFC |
|---|---|---|
| PETH | `plot_peth` (cell 15) — one panel per group/FOV, mean ± SEM, vertical event marker | `matplotlib` line plots with 1.96·SEM shading |
| Heatmap | `plot_heatmap` (cell 16) — sorted (neurons, time), RdBu_r if z-scored else Viridis, `zmid=0` | `matplotlib.imshow` with custom diverging cmap (PRGn_r), shared `±cmax` |
| Raster | `plot_trial_raster` (cell 17) — single neuron, all trials | n/a within scope (per-cluster rasters live downstream) |
| Library | Plotly (interactive) | Matplotlib + Seaborn + ProPlot |

---

## 4. Mathematical Significance of Each Divergence

### 4.1 Percentile baseline vs session mean (D1)

The 8th-percentile baseline (REACHER) is robust to transient excitations because percentile statistics are insensitive to the upper tail of the distribution. For a neuron whose firing is sparse, the 8th percentile is approximately the noise floor.

The arithmetic mean (PFC's `signals /= mean`) is *not* robust. If a neuron is task-driven for, say, 30 % of the session, the mean is pulled toward task-driven values. The denominator becomes too large, and apparent ΔF/F is compressed. Concretely, if true F₀ ≈ 1 (in raw units) and task-driven F̄ ≈ 1.5, the percentile baseline reports ΔF/F amplitudes of `(F − 1) / 1`, but the mean baseline reports `(F − 1) / 1.5` — a 33 % under-estimate of magnitude. **Cross-pipeline amplitude comparisons (peak ΔF/F, integrated response area, population trace height) are therefore not valid without recomputing on identically normalized traces.**

### 4.2 Z-score baseline scope (D2)

REACHER's `[-3000, -500] ms` window is 19 frames at 7.5 Hz — a small sample for σ estimation. If a neuron has anticipatory build-up before the event, that build-up contaminates the baseline std and can suppress apparent z-score amplitude.

PFC's full-session z-score uses ~thousands of frames for σ estimation, so the variance estimate is stable. But the variance is dominated by whichever epoch occupies the most frames — typically inter-trial intervals — which means the *task-period* z-scores look small relative to a *theoretical* "rest-only" z-score.

Neither is wrong; they answer different questions. The deliverable's worth recording: REACHER's z-score is about *how unusual is this for the pre-event period*; PFC's is *how unusual is this within this session.*

### 4.3 The 3-D z-score baseline bug in REACHER

```python
# cell 10, ZScore.apply, 3-D branch
start, end = 0, signals.shape[-1]   # entire window
baseline = signals[..., start:end]
```

The conceptual contract of `ZScore(window_ms=(-3000, -500))` is "use the pre-event window as baseline." The 3-D path silently violates the contract: post-event activity is included in the mean and std. The practical effect is that a strongly-driven neuron z-scores against its own response, suppressing the apparent post-event effect. The 2-D path (operating on full session signals) is correct; only the path that operates on already-windowed `(trials, neurons, time)` tensors is wrong.

Whether this bug is on or off the canonical execution path depends on whether `extract_event_windows` calls `ZScore` after windowing or before. Cell 11's `extract_event_windows` applies `window_pipeline` after stacking trials, so the buggy path **is** active when z-score is in the window pipeline.

### 4.4 Population SEM (REACHER)

`grand_sem = np.nanmean(sem_matrix, axis=0)` is the mean of per-FOV SEMs. By Jensen's inequality applied to the square-root, this differs from the pooled SEM `pooled_std / sqrt(N_total)`. The mean-of-SEMs is biased *low* relative to the true pooled SEM whenever sample sizes are unequal (which they typically are). The visual effect is unrealistically narrow shading on Population-view plots.

---

## 5. Identified Flaws & Methodological Hazards

### 5.1 REACHER

1. **Z-score 3-D path uses entire window as baseline (cell 10).** Verified by reading the source. Comment claims "0 = event onset" but `start = 0` is the first frame of the window. *Likely bug.*
2. **Population SEM is mean of per-FOV SEMs (cell 13), not pooled SEM.** Underestimates uncertainty.
3. **Frame-timestamp mismatch silently falls back to a synthetic regular grid (cell 7).** Tolerance is `±8 frames` or `±0.5 %`. A user whose timestamps fail this check loses trial-precise alignment without any warning printed.

### 5.2 PFC

1. **F / mean(F) is not ΔF/F (cell 2).** See §4.1. Cross-pipeline magnitude comparisons are invalid.
2. **`activeleverall[:300]` (cell 2)** silently caps active-lever trials to the first 300. No equivalent cap on inactive lever — n is asymmetric across conditions in a way that is invisible to readers.
3. **`separation_requirement = 1000 ms` (cell 1)** drops the *later* event in any pair < 1 s apart. Rationale not in the code or comments. Default-on for all analyses.
4. **Trials outside the valid frame range are deleted, not nan-padded.** Per-neuron trial counts vary; downstream `np.nanmean` hides this without flagging it.
5. **Per-trial baseline window is fixed at frames 0:22 = first 3 s of the pre-event window (cell 1, used in cell 6).** For event spacings shorter than 7 s, the baseline of trial *n+1* overlaps the response of trial *n*. The 1 s separation requirement does not protect against this.
6. **Hardcoded Windows-style absolute path** (`r'C:\Users\clark\...'`, cell 1). Notebook is not portable.

---

## 6. Reproducibility & Determinism

Within the shared scope, neither pipeline introduces nondeterminism (no RNG is touched in preprocessing, windowing, baseline subtraction, or population averaging on either side). Reproducibility concerns are therefore confined to code organization and path portability.

| Concern | REACHER | PFC |
|---|---|---|
| Hyperparameters in one place | Yes (cell 3) | Partial (cell 1 + scattered) |
| Re-runs deterministically within scope | Yes | Yes |
| Code encapsulated in functions | Yes | Mixed (long script-style cells) |
| Path portability | Relative `Path` from cell 3 default | Hardcoded Windows absolute path |

---

## 7. Recommendations

In rough order of impact (within the shared scope):

1. **Standardize the trace-level normalization.** Decide whether the canonical preprocessing is ΔF/F (percentile baseline) or F/⟨F⟩ (mean baseline). Quantify the cross-pipeline difference on a representative session: run both normalizations on identical events and compare population trace amplitudes side-by-side.
2. **Fix REACHER's 3-D z-score path** (cell 10). Replace the `start, end = 0, signals.shape[-1]` branch with a real pre-event slice computed from `frame_duration_ms` and the trial window's onset frame.
3. **Replace mean-of-SEMs with pooled SEM** in REACHER's Population view (cell 13). Compute `std(neuron_means, ddof=1) / sqrt(N_pool)` directly.
4. **Document or remove** `activeleverall[:300]` and `separation_requirement = 1000 ms`. If they encode a real scientific decision, write a sentence explaining why; if they were debugging shortcuts, remove them.
5. **Emit a warning** when REACHER's `load_fov_directory` (cell 7) silently falls back to a synthetic time grid.
6. **Drop the Windows-style absolute path** in PFC cell 1; parameterize via env var or `Path.home() / ...`.

---

## Appendix A — Hardcoded Constants

### REACHER (`reacher_analysis.ipynb`, cell 3)

| Constant | Default | Notes |
|---|---|---|
| `FPS` | 30.0 Hz | Raw acquisition rate |
| `FRAME_AVERAGING` | 4 | Effective FPS = 7.5 Hz |
| `PRE_S` / `POST_S` | 5.0 / 10.0 s | Configurable in widget |
| `BUFFER_MS` | 0 | Off by default |
| `MIN_TRIALS` | 3 | Minimum to include a Sample |
| `DFOF_PERCENTILE` | 8.0 | Baseline percentile |
| `ZSCORE_WINDOW_MS` | (−3000, −500) | Pre-event ms |
| `SMOOTHING_SIGMA` | 2.0 | Frames |
| Frame-timestamp tolerance | ±8 frames or ±0.5 % | Cell 7 |

### PFC (`...forestclusteringedit.ipynb`, cell 1)

Constants in scope (preprocessing → population trace) only; downstream analysis constants omitted.

| Constant | Default | Notes |
|---|---|---|
| `mineventstoanalyze` | 3 | Cell 1 |
| `delete_overlaps` | `'yes'` | Cell 1 |
| `separation_requirement` | 1000 ms | Cell 1 |
| `frameaveraging` | 4 | Cell 1 |
| `framerate` | 30 Hz | Cell 1 |
| `averagedframerate` | 7.5 Hz | Derived |
| `z_score_data` | `'yes'` | Cell 1 |
| `pre_window_size` | int(10·7.5) = 75 frames | 10 s |
| `window_size` | int(75·2 + 1.6·7.5) = 162 frames | 21.6 s |
| `post_window_size` | 87 frames | 11.6 s |
| `baselinefirstframe` | 0 | Cell 1 |
| `baselinelastframe` | int(3·7.5) = 22 | Cell 1 |
| `infusionframe` | int(75 + 1.6·7.5) = 87 | Cell 1 |
| `eventofinterest` | `'activeleverall'` | Cell 1 |
| `[:300]` cap | 300 | Cell 2, only on `activeleverall` |

---

## Appendix B — Cell Index Cross-Reference

### REACHER (`reacher_analysis.ipynb`)

| Cell | Topic |
|---|---|
| 0 | Imports |
| 1 | `REACHER_EVENT_DICT` |
| 2 | Color palette |
| 3 | Module-level constants |
| 5 | `load_xlsx_events` |
| 6 | `Sample` class |
| 7 | `load_fov_directory` (frame-timestamp tolerance) |
| 8 | `load_dataset` |
| 10 | `DFOverF`, `ZScore` (3-D bug), `GaussianSmoothing`, `Pipeline` |
| 11 | `extract_event_windows`, `trial_mean_sem` |
| 12 | `sort_neuron_matrix` |
| 13 | `compute_for_view` (population SEM) |
| 14 | Ipywidgets UI |
| 15 | `plot_peth` |
| 16 | `plot_heatmap` |
| 17 | `plot_trial_raster` |
| 18 | Execution flow |

### PFC (`...forestclusteringedit.ipynb`)

In-scope cells only. Downstream cells (auROC, BH-FDR, spectral / RF clustering, per-cluster visualization, stability, day-to-day tracking, behavior correlations) are not listed.

| Cell | Topic |
|---|---|
| 0 | Imports |
| 1 | Hardcoded constants (preprocessing + windowing) |
| 2 | `analyze_single_session` (loading, multi-part concat, de-dup, F/⟨F⟩, `[:300]` cap, full-session z-score) |
| 6 | Per-trial baseline subtraction (the `alignedevents` step) |
| 8 | Population heatmap visualization of z-scored signals |

---

*End of comparison.*
