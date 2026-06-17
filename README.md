# Axplorer — Neural Data Analysis Pipeline

**Standardized EDA pipeline for aligned neural and behavioral data**

[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://github.com/thejoshbq/neural-eda)
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Phoxel Workbench](https://img.shields.io/badge/Phoxel_Workbench-member-orange)](https://github.com/Otis-Lab-MUSC)

*Written by*: Joshua Boquiren

[![](https://img.shields.io/badge/@thejoshbq-grey?style=flat&logo=github)](https://github.com/thejoshbq)

---

## Overview

Calcium imaging experiments produce two parallel data streams: a matrix of fluorescence traces (one per neuron, thousands of frames) and an event log of timestamped behavioral events (lever presses, infusions, licks). Turning these into peri-event analyses requires aligning timescales, normalizing signals, windowing around events, computing statistics, and generating publication-quality figures — a process that is tedious, error-prone, and difficult to reproduce when done ad hoc.

Axplorer is a validated ingestion-to-export pipeline that standardizes this workflow. It loads raw `.npy` signal files and `.xlsx` / `.mat` event logs, validates their structure, aligns neural and behavioral timescales via [Pynapse](https://github.com/thejoshbq/pynapse), applies configurable preprocessing (DF/F, Z-score, smoothing), computes peri-event time histograms and response metrics, and exports results as figures, CSVs, or HDF5 archives.

The project has two components. The **`axplorer` library** provides a scriptable Python API for batch analysis and custom workflows. The **interactive dashboard** wraps that library in a FastAPI + React interface with point-and-click configuration, real-time visualization, and one-click export — no code required.

Axplorer supports three task paradigms: `reacher` (operant reaching with Excel-based event logs), `legacy_her` (heroin self-administration with MATLAB event logs), and `legacy_eth` (ethanol self-administration with MATLAB event logs). Task type can be specified manually or auto-detected from the event file format.

> **Pipeline flow:** `Upload → Validate → Align → Preprocess → Analyze → Visualize → Export`

## Features

### Ingestion & Validation
- Validates `.npy` signal files (shape, dtype, NaN/Inf checks)
- Validates `.xlsx` event files (required sheets and columns) and `.mat` event files (required keys)
- Auto-detects task type from event file format and contents
- Frame alignment verification between signal and timestamp counts

### Preprocessing
- **DF/F normalization** — baseline percentile-based fluorescence normalization
- **Z-score normalization** — baseline window mean/SD normalization
- **Gaussian smoothing** — temporal noise reduction with configurable kernel width
- All steps applied per peri-event window, not globally

### Analysis
- **Peri-event time histograms (PETH)** — trial-averaged mean ± SEM traces per neuron
- **Sorted heatmaps** — neurons ordered by peak latency, trough latency, or magnitude
- **Single-cell trial rasters** — trial-by-trial activity for individual neurons
- **Response classification** — neurons labeled as excitatory, inhibitory, or non-responsive based on peak Z-score thresholds
- **Response metrics** — peak Z-score, peak latency, AUC, onset latency, baseline/response means
- **Behavioral summary** — active/inactive/timeout press counts, reinforcer count, discrimination index, press rate, cumulative press curves

### Dashboard
- Three-panel layout: Upload, Analysis Controls, Export
- Sidebar with upload zone, session configuration, preprocessing toggles, and peri-event parameter controls
- Dark-themed UI built on React 19 + Tailwind CSS with glass morphism and Reacher cyan accent

### Export
- **Figures** — PNG, SVG, or PDF via Kaleido with configurable resolution
- **Data** — PETH mean ± SEM as CSV
- **Archives** — Full session results (metadata + all event PETHs) as HDF5

## Dashboard

The dashboard is a React 19 single-page application served by the FastAPI backend, organized into three panels accessible after loading a session:

**Session Overview** — Displays session metadata (neuron count, frame count, duration, event counts) and behavioral summary statistics including discrimination index, press rates, and cumulative press curves.

**Peri-Event Explorer** — The main analysis workspace. Select an event type and neuron subset, configure pre/post-event windows, and click Recompute to generate PETH traces, sorted heatmaps, and trial rasters. All preprocessing parameters are adjustable in the sidebar. Charts are rendered with Plotly via react-plotly.js.

**Export** — Download figures and data from the current analysis. Supports PNG/SVG/PDF for figures, CSV for PETH data, and HDF5 for full session archives.

## Installation

### Prerequisites

- **Python >=3.10**
- **Pynapse** — Axplorer's neural data backend. Pynapse is not published on PyPI; install it from a local clone:

```bash
# Clone pynapse (if you haven't already)
git clone https://github.com/thejoshbq/pynapse.git /path/to/pynapse
pip install -e /path/to/pynapse
```

### Install Axplorer

```bash
git clone https://github.com/thejoshbq/neural-eda.git
cd neural-eda
pip install -e .
```

### Development

```bash
pip install -e ".[dev]"
```

This adds `pytest` and `pytest-cov` for running the test suite.

To work on the dashboard with hot reload, start the backend and Vite together:

```bash
./scripts/dev.sh
```

This runs `uvicorn api.app:app --reload` on `:8050` and the Vite dev server on `:5173`, then opens `http://localhost:5173`. Vite proxies `/api/*` to the backend. `Ctrl-C` stops both. Use plain `axplorer` only after `cd web && npm run build`; that command serves the pre-built bundle from `web/dist/` and does not pick up frontend source changes.

## Quick Start

1. **Launch the dashboard:**
   ```bash
   axplorer
   ```
   Opens at `http://localhost:8050`.

2. **Upload files** — Drag or select a `.npy` signal file and an `.xlsx` or `.mat` event file in the sidebar upload zone.

3. **Configure session** — Set the imaging FPS, frame averaging factor, and task type (or leave on Auto-Detect).

4. **Load Session** — Click the Load Session button. The Session Overview tab populates with metadata and behavioral metrics.

5. **Explore** — Switch to the Peri-Event Explorer tab. Select an event type and cells, adjust pre/post-event windows and preprocessing, then click Recompute.

6. **Export** — Switch to the Export tab. Select a format and download figures or data.

## Input Data

### Signal File (`.npy`)

A 2-D NumPy array of fluorescence traces.

| Property | Requirement |
|---|---|
| Format | `.npy` (saved with `numpy.save`) |
| Shape | `(neurons, frames)` — axis 0 < axis 1 |
| Dtype | Any numeric type (float32 recommended) |
| Values | No NaN or Inf allowed |

### Event File (`.xlsx`)

An Excel workbook with behavioral event timestamps.

| Property | Requirement |
|---|---|
| Required sheet | `Behavior Data` |
| Required columns | `device`, `event`, `start_timestamp`, `end_timestamp` |

### Event File (`.mat`)

A MATLAB struct exported from legacy acquisition systems.

| Property | Requirement |
|---|---|
| Required key | `eventlog` |

### Task Types

| Task Type | Event Format | Detection Rule | Paradigm |
|---|---|---|---|
| `reacher` | `.xlsx` | Any `.xlsx` file | Operant reaching |
| `legacy_her` | `.mat` | `.mat` without event codes 50/51 | Heroin self-administration |
| `legacy_eth` | `.mat` | `.mat` with event codes 50 or 51 | Ethanol self-administration |

## Architecture

### Pipeline Flow

```
 ┌─────────────┐    ┌─────────────┐    ┌────────────────┐
 │  .npy file  │    │ .xlsx/.mat  │    │  User Config   │
 │  (signals)  │    │  (events)   │    │ (FPS, task...) │
 └──────┬──────┘    └──────┬──────┘    └───────┬────────┘
        │                  │                   │
        ▼                  ▼                   │
 ┌──────────────────────────────┐              │
 │  validate_signal_file()      │              │
 │  validate_event_file()       │              │
 │  detect_task_type()          │              │
 └──────────────┬───────────────┘              │
                │                              │
                ▼                              │
 ┌──────────────────────────────┐              │
 │  load_session_files()        │◄─────────────┘
 │  → Sample + SessionMetadata  │
 └──────────────┬───────────────┘
                │
                ▼
 ┌──────────────────────────────┐
 │  SessionWrapper              │
 │  ├─ build_pipeline()         │
 │  └─ get_tensor()             │
 └──────────────┬───────────────┘
                │
          ┌─────┴─────┐
          ▼           ▼
 ┌─────────────┐ ┌──────────────────┐
 │compute_peth │ │compute_behavior_ │
 │             │ │summary           │
 └──────┬──────┘ └──────────────────┘
        │
   ┌────┴────┐
   ▼         ▼
┌────────┐ ┌───────────────────────┐
│Heatmap │ │compute_response_      │
│Sorting │ │metrics / classify     │
└────────┘ └───────────────────────┘
        │
        ▼
 ┌──────────────────────────────┐
 │  Export                      │
 │  ├─ export_figure()          │
 │  ├─ export_peth_csv()        │
 │  └─ export_session_hdf5()    │
 └──────────────────────────────┘
```

### Project Structure

```
neural-eda/
├── pyproject.toml                          # Package config, deps, entry point
├── axplorer/                               # Analysis library
│   ├── __init__.py
│   ├── types.py                            # Data contracts (dataclasses)
│   ├── alignment/
│   │   ├── __init__.py
│   │   └── session.py                      # SessionWrapper over Pynapse Sample
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── behavior.py                     # BehaviorSummary computation
│   │   ├── peth.py                         # PETH, sorted heatmaps, trial rasters
│   │   └── response.py                     # Response metrics & classification
│   ├── export/
│   │   ├── __init__.py                     # Public API: export_figure, export_peth_csv, export_session_hdf5
│   │   ├── data.py                         # CSV and HDF5 export
│   │   └── figures.py                      # Figure export (PNG/SVG/PDF)
│   └── ingestion/
│       ├── __init__.py
│       ├── loader.py                       # load_session_files(), LoadError
│       └── validators.py                   # File validation & task-type detection
├── api/                                    # FastAPI backend
│   ├── app.py                              # FastAPI app, uvicorn entry
│   ├── state.py                            # DataStore — server-side state
│   └── routers/
│       ├── upload.py                       # POST /api/load, GET /api/status
│       ├── analysis.py                     # POST /api/compute
│       └── export.py                       # POST /api/export/figure, /data
├── web/                                    # React 19 + Vite 6 + Tailwind
│   └── src/                                # Components, Zustand stores, Plotly charts
└── tests/
    ├── __init__.py
    ├── conftest.py                         # Shared fixtures (synthetic samples, temp files)
    ├── test_behavior.py                    # → axplorer/analysis/behavior.py
    ├── test_export.py                      # → axplorer/export/
    ├── test_loader.py                      # → axplorer/ingestion/loader.py
    ├── test_peth.py                        # → axplorer/analysis/peth.py
    ├── test_response.py                    # → axplorer/analysis/response.py
    ├── test_session.py                     # → axplorer/alignment/session.py
    └── test_validators.py                  # → axplorer/ingestion/validators.py
```

### Key Data Types

Defined in `axplorer/types.py`:

| Type | Purpose | Key Fields |
|---|---|---|
| `SessionMetadata` | Immutable session summary | `name`, `n_neurons`, `n_frames`, `n_events`, `event_counts`, `effective_fps`, `duration_s`, `task_type` |
| `PETHResult` | PETH for one event across neurons | `event_windows` *(trials, neurons, time)*, `time_axis`, `mean` *(neurons, time)*, `sem` *(neurons, time)*, `event_label`, `n_trials`, `pre_event_s`, `post_event_s` |
| `ResponseMetrics` | Per-neuron response quantification | `cell_id`, `peak_zscore`, `peak_latency_s`, `auc`, `onset_latency_s`, `mean_baseline`, `mean_response` |
| `BehaviorSummary` | Aggregate behavioral metrics | `active_presses`, `inactive_presses`, `timeout_presses`, `reinforcers`, `discrimination_index`, `press_rate_per_min`, `event_timeline`, `cumulative_presses` |

### Pynapse Dependency

Axplorer delegates all low-level neural data operations to [Pynapse](https://github.com/thejoshbq/pynapse), a separate library that handles event log parsing, signal-event alignment, frame-trigger extraction, and peri-event tensor construction. Axplorer wraps Pynapse's `Sample` object via `SessionWrapper` and builds its preprocessing pipelines from Pynapse's `Pipeline`, `DFOverF`, `ZScore`, and `GaussianSmoothing` primitives. This design avoids reimplementing validated core logic while providing a higher-level, dashboard-friendly API.

## Preprocessing

All preprocessing steps are applied **per peri-event window** (not to the full session trace), ensuring that each trial's baseline is computed from its own pre-event epoch.

### DF/F (Delta F over F)

Normalizes fluorescence by a baseline percentile. For each window, the baseline is the *n*-th percentile of the raw trace, and the normalized signal is `(F - F_baseline) / F_baseline`.

- **Default percentile:** 8
- **Range:** 1–50

A low percentile (e.g., 8th) captures the quiescent fluorescence floor, making the metric robust to transient calcium events inflating the baseline estimate.

### Z-Score

Normalizes each window to baseline mean and standard deviation. For a given pre-event baseline window, the signal is transformed as `(F - μ_baseline) / σ_baseline`, expressing activity in units of baseline standard deviations.

- **Default window:** -3000 to -500 ms (relative to event onset)

The window is set to end 500 ms before the event to avoid contamination from anticipatory or peri-onset activity.

### Gaussian Smoothing

Applies a 1-D Gaussian kernel along the time axis to reduce frame-to-frame noise while preserving the temporal structure of calcium transients.

- **Default sigma:** 2 frames
- **Range:** 0.5–5 frames

## Configuration Reference

All parameters are accessible in the dashboard sidebar. Default values match the corresponding function signatures in the library API.

### Session Config

| Parameter | ID | Default | Range | Step | Description |
|---|---|---|---|---|---|
| FPS | `input-fps` | 30 | 1–1000 | 1 | Raw imaging frame rate (Hz) |
| Frame Avg | `input-frame-avg` | 4 | 1–100 | 1 | Number of raw frames binned per signal frame |
| Task Type | `dropdown-task-type` | Auto-Detect | auto / reacher / legacy_her / legacy_eth | — | Behavioral paradigm |

### Preprocessing

| Parameter | ID | Default | Range | Step | Description |
|---|---|---|---|---|---|
| DF/F | `check-dfof` | Enabled | — | — | Toggle DF/F normalization |
| DF/F Percentile | `slider-dfof-pct` | 8 | 1–50 | 1 | Baseline percentile for DF/F |
| Z-Score | `check-zscore` | Enabled | — | — | Toggle Z-score normalization |
| Z-Score Start (ms) | `input-zscore-start` | -3000 | — | — | Start of baseline window (ms relative to event) |
| Z-Score End (ms) | `input-zscore-end` | -500 | — | — | End of baseline window (ms relative to event) |
| Smoothing | `check-smooth` | Enabled | — | — | Toggle Gaussian smoothing |
| Smoothing Sigma | `slider-smooth-sigma` | 2 | 0.5–5 | 0.5 | Gaussian kernel width (frames) |

### Peri-Event

| Parameter | ID | Default | Range | Step | Description |
|---|---|---|---|---|---|
| Event | `dropdown-event` | — | *dynamic* | — | Event type to lock analysis windows to |
| Cells | `dropdown-cells` | — | *dynamic* | — | Neuron subset (multi-select) |
| Pre-Event (s) | `slider-pre-event` | 5 | 0.5–10 | 0.5 | Seconds before event onset |
| Post-Event (s) | `slider-post-event` | 10 | 0.5–20 | 0.5 | Seconds after event onset |
| Buffer (ms) | `input-buffer-ms` | 0 | 0+ | 1 | Minimum interval between events; closer events excluded |
| Min Trials | `input-min-trials` | 3 | 1+ | 1 | Minimum valid trials required for analysis |

## Library API

The `axplorer` library can be used independently of the dashboard for scripted or batch analysis:

```python
from axplorer.ingestion import load_session_files
from axplorer.alignment import SessionWrapper
from axplorer.analysis.peth import compute_peth
from axplorer.analysis.response import compute_response_metrics, classify_response
from axplorer.export import export_peth_csv

# 1. Load and validate session files
sample, metadata = load_session_files(
    signal_path="session_01.npy",
    event_path="session_01.xlsx",
    fps=30.0,
    frame_averaging=4,
    # task_type=None → auto-detect
)

# 2. Wrap the sample for pipeline construction
session = SessionWrapper(sample)

# 3. Build a preprocessing pipeline
pipeline = session.build_pipeline(
    dfof_percentile=8.0,
    zscore_window_ms=(-3000.0, -500.0),
    smoothing_sigma=2.0,
)

# 4. Compute PETH for an event type
event_code = session.get_event_code_for_label("active_lever_press")
peth = compute_peth(
    session=session,
    event_id=event_code,
    pre_event_s=5.0,
    post_event_s=10.0,
    pipeline=pipeline,
    min_trials=3,
)

# 5. Quantify and classify neuronal responses
metrics = compute_response_metrics(peth)
for m in metrics:
    label = classify_response(m)
    print(f"Cell {m.cell_id}: {label} (peak z={m.peak_zscore:.2f}, AUC={m.auc:.2f})")

# 6. Export
export_peth_csv(peth, path="session_01_peth.csv")
```

## Testing

The test suite uses synthetic data fixtures defined in `tests/conftest.py` — no real experimental data is required.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov
```

### Test Module Mapping

| Test File | Covers |
|---|---|
| `test_validators.py` | `axplorer/ingestion/validators.py` |
| `test_loader.py` | `axplorer/ingestion/loader.py` |
| `test_session.py` | `axplorer/alignment/session.py` |
| `test_peth.py` | `axplorer/analysis/peth.py` |
| `test_response.py` | `axplorer/analysis/response.py` |
| `test_behavior.py` | `axplorer/analysis/behavior.py` |
| `test_export.py` | `axplorer/export/` |

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| numpy | >=1.24 | Array operations, signal processing |
| pandas | >=2.0 | Event data manipulation, CSV export |
| scipy | >=1.10 | Gaussian smoothing, MATLAB file loading |
| openpyxl | >=3.1 | Excel event file reading |
| plotly | >=5.18 | Interactive figures |
| fastapi | >=0.104 | Backend REST API |
| uvicorn[standard] | >=0.24 | ASGI server |
| kaleido | >=0.2 | Static figure export (PNG/SVG/PDF) |
| h5py | >=3.9 | HDF5 export |
| pynapse | local | Neural data backend (event parsing, alignment, tensors) |

Dev dependencies: `pytest >=7.4`, `pytest-cov >=4.1`

## Glossary

| Term | Definition |
|---|---|
| **AUC** | Area under the curve. Trapezoidal integral of the neural response above baseline within a defined time window. Measures total response magnitude. |
| **Calcium imaging** | Optical technique that uses fluorescent indicators to record neural activity. Changes in intracellular calcium concentration produce changes in fluorescence intensity. |
| **DF/F** | Delta F over F. Fluorescence normalization method: `(F - F₀) / F₀`, where F₀ is a baseline estimate (e.g., the 8th percentile of the trace). |
| **Discrimination index** | Ratio of active presses to total presses (active + inactive). Ranges from 0 to 1; values near 1 indicate strong preference for the active operandum. |
| **Frame averaging** | Temporal binning of raw imaging frames. If the microscope acquires at 120 Hz but frames are averaged in groups of 4, the effective signal rate is 30 Hz. |
| **Head-fixed** | Experimental preparation in which the animal's head is mechanically immobilized during imaging, enabling stable optical access for calcium imaging. |
| **PETH** | Peri-event time histogram. Time-locked average of neural activity aligned to a behavioral event (e.g., lever press). Shows the mean ± SEM response profile across trials. |
| **SEM** | Standard error of the mean. `SEM = SD / √n`, where *n* is the number of trials. Quantifies trial-to-trial variability of the average response. |
| **Z-score** | Standardized score: `(x - μ) / σ`, where μ and σ are the mean and standard deviation of a baseline epoch. Expresses activity in units of baseline variability. |

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Contact

Joshua Boquiren — [thejoshbq@proton.me](mailto:thejoshbq@proton.me)

[GitHub: thejoshbq/neural-eda](https://github.com/thejoshbq/neural-eda)
