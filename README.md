# Axplorer — Peri-Event Analysis Pipeline

**Standardized exploratory analysis of aligned calcium imaging and behavioral data, from raw traces to publication figures.**

[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://github.com/thejoshbq/axplorer/releases)
[![Language](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Phoxel Workbench](https://img.shields.io/badge/Phoxel_Workbench-member-orange)](https://github.com/Otis-Lab-MUSC)

*Written by*: Joshua Boquiren

[![](https://img.shields.io/badge/@thejoshbq-grey?style=flat&logo=github)](https://github.com/thejoshbq)

---

## Overview

A calcium imaging experiment leaves you with two parallel records: fluorescence traces for every detected neuron, and a timestamped log of what the animal did. Axplorer takes both — `.npy` traces alongside Excel or MATLAB event logs — validates them, puts them on a common timescale, and answers the question that follows: how does each neuron's activity change around a lever press, an infusion, or a reward? It produces peri-event time histograms, per-neuron response metrics, sorted heatmaps, and behavioral summaries, and exports them as figures (PNG, SVG, PDF) or data (CSV, HDF5) ready for a manuscript.

Normalization (DF/F, Z-score, Gaussian smoothing) is configurable and applied within each peri-event window rather than across the whole recording, so a baseline drawn hours into a session does not distort an early trial. Three task paradigms are supported and auto-detected from the event file: operant reaching (`reacher`), heroin self-administration (`legacy_her`), and ethanol self-administration (`legacy_eth`). Alignment and signal handling come from [pynapse](https://github.com/thejoshbq/pynapse), which Axplorer wraps rather than reimplements, so traces curated in [ROI G. Biv](https://github.com/thejoshbq/roigbiv) carry through the whole chain without reformatting. Analyses can be run as a scriptable Python API for batch work, or through an interactive dashboard for point-and-click exploration.

---

## Getting Started

Axplorer depends on pynapse as a local path dependency, so clone it alongside this repository first:

```bash
git clone git@github.com:thejoshbq/pynapse.git
git clone git@github.com:thejoshbq/axplorer.git
cd axplorer
pip install -e .
axplorer
```

The `axplorer` command serves the dashboard at `http://localhost:8050`.

---

## Architecture & Dependencies

| Component | Language | Framework / Libraries |
|---|---|---|
| Analysis pipeline | Python 3.10+ | pynapse, NumPy, SciPy, pandas |
| Ingestion & validation | Python 3.10+ | NumPy, pandas, openpyxl |
| Backend API | Python 3.10+ | FastAPI, Uvicorn, python-multipart |
| Dashboard | TypeScript | React 19, Vite, Tailwind CSS, Zustand, react-plotly.js |
| Export & figures | Python 3.10+ | Plotly, Kaleido, h5py, PyTables |

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Contact

Joshua Boquiren — [thejoshbq@proton.me](mailto:thejoshbq@proton.me)

[GitHub: thejoshbq/axplorer](https://github.com/thejoshbq/axplorer)
