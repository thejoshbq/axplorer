# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (editable, with dev deps)
pip install -e ".[dev]"

# Pynapse must be installed separately (not on PyPI)
pip install -e /path/to/pynapse

# Run app (FastAPI backend + React frontend)
axplorer                      # launches app at localhost:8050

# Frontend development
cd web && npm install         # install JS dependencies
cd web && npm run dev         # dev server on :5173, proxies /api to :8050
cd web && npm run build       # production build to web/dist/

# Tests
pytest                        # runs all tests (verbose, short tracebacks via pyproject.toml)
pytest --cov                  # with coverage
pytest tests/test_peth.py     # single module
pytest tests/test_peth.py::TestComputePeth::test_basic_peth -v  # single test
```

## Architecture

Three packages: **`axplorer`** (scriptable analysis library), **`api`** (FastAPI backend wrapping axplorer), and **`web`** (React 19 + Vite + Tailwind frontend).

The `axplorer` CLI command runs `api.app:main` which serves the FastAPI backend on port 8050 and opens the browser. The built React frontend is served as static files from `web/dist/`.

### API Layer (`api/`)

- **`api/state.py`** -- `DataStore` class holding data hierarchy and loaded sessions (plain Python class, no param dependency).
- **`api/routers/upload.py`** -- `POST /api/load` loads data, `GET /api/status` returns current state.
- **`api/routers/analysis.py`** -- `POST /api/compute` computes PETH data, returns JSON with plots and shared y-range.
- **`api/routers/export.py`** -- `POST /api/export/figure` and `POST /api/export/data` for file downloads.
- **`api/app.py`** -- FastAPI app creation, router registration, static file serving, uvicorn entry point.

### Frontend (`web/`)

- React 19 + Vite 6 + Tailwind 3.4 + TypeScript
- Zustand stores: `useThemeStore`, `useDataStore`, `useAnalysisStore`, `usePlotStore`
- Plotly charts via `react-plotly.js` with `plotly.js-cartesian-dist-min` (minimal bundle)
- Reacher theme: cyan accent (#00D4D8), JetBrains Mono font, neon-grid background, glass morphism
- Dark/light mode toggle re-themes both UI and Plotly charts

### Data Flow

```
Upload -> validate (ingestion/validators.py) -> load_session_files() -> Sample + SessionMetadata
  -> SessionWrapper (alignment/session.py) -> build_pipeline() + get_tensor()
    -> compute_peth() / compute_behavior_summary() -> compute_response_metrics() / classify_response()
      -> export_figure() / export_peth_csv() / export_session_hdf5()
```

### Pynapse Dependency

Axplorer wraps -- never reimplements -- Pynapse's core objects. `SessionWrapper` wraps `pynapse.core.Sample`. Preprocessing pipelines are built from Pynapse's `Pipeline`, `DFOverF`, `ZScore`, `GaussianSmoothing`. Peri-event tensors come from `Sample.get_tensor()`. Event dictionaries are resolved via `pynapse.config.events.TASK_TO_DICT`.

### Data Contracts

`axplorer/types.py` defines four frozen/mutable dataclasses that form the pipeline's type boundaries: `SessionMetadata`, `PETHResult`, `ResponseMetrics`, `BehaviorSummary`. All analysis functions accept and return these types.

### Task Types

Three supported paradigms: `reacher` (.xlsx events), `legacy_her` (.mat), `legacy_eth` (.mat with event codes 50/51). Auto-detection logic is in `ingestion/validators.py:detect_task_type()`.

## Conventions

- Python >=3.10. Type hints on all function signatures.
- Google-style docstrings on all modules, classes, and functions.
- Absolute imports throughout (e.g., `from axplorer.analysis.peth import compute_peth`).
- Tests use class-based organization (`class TestComputePeth:`) with pytest fixtures from `tests/conftest.py` providing synthetic data (no real experimental data needed).
- `LoadError` (in `ingestion/loader.py`) accumulates all validation errors before raising, rather than failing on the first error.
