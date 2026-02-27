# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (editable, with dev deps)
pip install -e ".[dev]"

# Pynapse must be installed separately (not on PyPI)
pip install -e /path/to/pynapse

# Run dashboard
axplorer                      # launches Dash app at localhost:8050

# Tests
pytest                        # runs all tests (verbose, short tracebacks via pyproject.toml)
pytest --cov                  # with coverage
pytest tests/test_peth.py     # single module
pytest tests/test_peth.py::TestComputePeth::test_basic_peth -v  # single test
```

## Architecture

Two packages: **`axplorer`** (scriptable analysis library) and **`dashboard`** (Plotly Dash UI wrapping axplorer). The entry point `axplorer` CLI command runs `dashboard.app:main`.

### Data Flow

```
Upload → validate (ingestion/validators.py) → load_session_files() → Sample + SessionMetadata
  → SessionWrapper (alignment/session.py) → build_pipeline() + get_tensor()
    → compute_peth() / compute_behavior_summary() → compute_response_metrics() / classify_response()
      → export_figure() / export_peth_csv() / export_session_hdf5()
```

### Pynapse Dependency

Axplorer wraps — never reimplements — Pynapse's core objects. `SessionWrapper` wraps `pynapse.core.Sample`. Preprocessing pipelines are built from Pynapse's `Pipeline`, `DFOverF`, `ZScore`, `GaussianSmoothing`. Peri-event tensors come from `Sample.get_tensor()`. Event dictionaries are resolved via `pynapse.config.events.TASK_TO_DICT`.

### Dashboard Patterns

- **State:** `dashboard/state.py` is an in-memory UUID-keyed store mapping browser session tokens to `SessionWrapper` objects.
- **Callbacks:** Each tab has a `dashboard/callbacks/*_cb.py` module exposing `register_*_callbacks(app)`. All are registered via `register_all_callbacks()` in `callbacks/__init__.py`.
- **Layouts:** `dashboard/layouts/__init__.py` assembles sidebar (col-3) + tabbed main area (col-9). Three tabs: Session Overview, Peri-Event Explorer, Export.
- **Theme:** Dark theme (DARKLY bootstrap + custom `axplorer_dark` Plotly template) defined in `dashboard/theme.py`. Event color overrides also live there.

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
