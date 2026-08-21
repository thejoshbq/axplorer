# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (editable, with dev deps). Pynapse is pinned as a file:// dep in
# pyproject.toml at /home/thejoshbq/Otis-Lab/Projects/Phoxel-Workbench/pynapse;
# editing pynapse picks up automatically since both are installed editable.
pip install -e ".[dev]"

# Run app (serves pre-built web/dist/ -- rebuild the frontend first if you changed it)
axplorer                      # launches at localhost:8050 and opens browser

# Dev mode (recommended while editing): backend + Vite together
./scripts/dev.sh              # uvicorn --reload :8050 + vite :5173 (proxies /api → :8050)

# Frontend only (needs backend running on :8050)
cd web && npm install
cd web && npm run dev         # :5173
cd web && npm run build       # writes web/dist/

# Tests (pyproject sets -v --tb=short)
pytest
pytest --cov
pytest tests/test_peth.py
pytest tests/test_peth.py::TestComputePeth::test_basic_peth -v
```

`scripts/dev.sh` pre-flights port 8050 and aborts if anything else owns it; both children run in their own process group so Ctrl-C kills the whole tree.

## Architecture

Three top-level packages: **`axplorer/`** (scriptable analysis library), **`api/`** (FastAPI backend wrapping axplorer), **`web/`** (React 19 + Vite + Tailwind frontend).

The `axplorer` console script runs `api.app:main`, which serves FastAPI on :8050 and mounts the built React frontend (`web/dist/`) as static files at `/`.

### Two ingestion sources

`DataStore.source` toggles between two backends that produce the same hierarchy shape `{population: {sample: [SessionWrapper, ...]}}`:

- **`filesystem`** — walks `{phase}/{animal_id}/{fov}/` directories. Each FOV must contain `*extractedsignals_raw.npy` and a behavioral event file. Event-file priority: REACHER `behavior_events*.csv` → legacy `.mat` → legacy `.xlsx`. Optional sibling `frame_timestamps.csv` is auto-picked-up so event→frame alignment uses real acquisition timestamps. Discovery: `axplorer/ingestion/discovery.py:discover_sessions()`. Sex is parsed from the trailing `M`/`F` of `animal_id`.
- **`database`** — `axplorer/ingestion/db_loader.py:load_db_hierarchy()` reads `DBSample` objects from a pynapse DuckDB file (default `~/.pynapse/pynapse.duckdb`). Returns `(hierarchy, conn)` — `DataStore` owns the open connection and closes it when reloading.

### Data levels

`DataStore.data_level` controls the granularity of `data_paths`:

| Level | Meaning |
|---|---|
| `Project` | One root path; walk full `{phase}/{animal_id}/{fov}/` tree. |
| `Population` | Each path is a population dir with sample subdirs. |
| `Sample` | Each path is a sample dir with FOV subdirs. |
| `FOV` | Each path is a single FOV dir. |
| `Files` | Raw `.npy` + event-file paths, loaded as one synthetic FOV. |

`Files`/`FOV` mode collapses to the synthetic `default/default/...` namespace so downstream code never needs to special-case missing hierarchy.

### API Layer (`api/`)

- **`api/state.py`** — `DataStore` holds hierarchy, all wrappers, available events (intersection across wrappers), and the open DuckDB connection. Plain Python class, no `param` dependency.
- **`api/routers/upload.py`** — `POST /api/load`, `GET /api/status`.
- **`api/routers/analysis.py`** — `POST /api/compute` returns PETH JSON with shared y-range.
- **`api/routers/export.py`** — `POST /api/export/figure`, `POST /api/export/data`.
- **`api/routers/browse.py`** — `GET /api/browse?path=...` for server-side directory navigation in the upload UI; restricted to the user's home directory and recognizes `.duckdb`/`.npy`/`.mat`/`.xlsx`.
- **`api/app.py`** — FastAPI app, router registration, static mount, `main()` entry point.

### Scriptable analysis API

`axplorer/dataset.py` exposes `Dataset` and `load_dataset()` for notebook/batch use. `Dataset.filter(...)` returns a new dataset by `SessionMeta` field equality (`phase`, `animal_id`, `sex`, `fov`, `is_tracked`). `Dataset.process_all(fn, n_jobs=...)` loads each session and applies `fn`; `n_jobs > 1` uses `ProcessPoolExecutor` and logs/skips failed sessions as `None`. Loading happens in the worker so the parent doesn't pay memory for the full dataset.

### Frontend (`web/`)

- React 19 + Vite 6 + Tailwind 3.4 + TypeScript
- Zustand stores: `useThemeStore`, `useDataStore`, `useAnalysisStore`, `usePlotStore`
- Plotly via `react-plotly.js` with `plotly.js-cartesian-dist-min` (minimal bundle)
- Reacher theme: cyan accent `#00D4D8`, JetBrains Mono, neon-grid background, glass morphism. Dark/light toggle re-themes both UI and Plotly traces.

### Data Flow

```
Upload → validate (ingestion/validators.py) → load_session_files() → Sample + SessionMetadata
  → SessionWrapper (alignment/session.py) → build_pipeline() + get_tensor()
    → compute_peth() / compute_behavior_summary() → compute_response_metrics() / classify_response()
      → export_figure() / export_peth_csv() / export_session_hdf5()
```

### Pynapse Dependency

Axplorer wraps — never reimplements — Pynapse's core objects. `SessionWrapper` wraps `pynapse.core.Sample` (or `pynapse.db.hydrate.DBSample` for the DB backend). Preprocessing is built from Pynapse's `Pipeline`, `DFOverF`, `ZScore`, `GaussianSmoothing`. Peri-event tensors come from `Sample.get_tensor()`. Event dictionaries are resolved via `pynapse.config.events.TASK_TO_DICT`.

### Data Contracts

`axplorer/types.py` defines the type boundaries — all analysis functions accept and return these:

- `SessionMeta` (frozen) — filesystem metadata (phase, animal_id, sex, fov, paths)
- `Session` — composed `(SessionMeta, SessionMetadata, SessionWrapper)`
- `SessionMetadata` (frozen) — loaded-session summary (counts, fps, duration, task_type)
- `PETHResult` — single-event peri-event histogram across neurons
- `PopulationPETHResult` — pooled + session-averaged PETH across multiple sessions
- `ResponseMetrics` — per-neuron peak/AUC/onset/baseline
- `BehaviorSummary` — press counts, discrimination index, cumulative-press curves

### Task Types

Three paradigms: `reacher` (.csv/.xlsx events), `legacy_her` (.mat), `legacy_eth` (.mat with event codes 50/51). Auto-detection: `ingestion/validators.py:detect_task_type()`. Override per-load via the `task_type` argument.

## Conventions

- Python ≥ 3.10. Type hints on all function signatures.
- Google-style docstrings on all modules, classes, and functions.
- Absolute imports throughout (e.g., `from axplorer.analysis.peth import compute_peth`).
- Tests use class-based organization (`class TestComputePeth:`) with pytest fixtures from `tests/conftest.py` providing synthetic data — no real experimental data needed.
- `LoadError` (in `ingestion/loader.py`) accumulates all validation errors before raising rather than failing on the first one.
