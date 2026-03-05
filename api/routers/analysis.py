"""Analysis router -- compute PETH data."""

from __future__ import annotations

import logging

import numpy as np
from pydantic import BaseModel
from fastapi import APIRouter

from axplorer.analysis.peth import compute_peth
from axplorer.analysis.population import compute_population_peth
from api.routers.upload import get_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])


class ComputeRequest(BaseModel):
    event_label: str
    view_level: str = "Population"
    pre_event_s: float = 5.0
    post_event_s: float = 10.0
    enable_dfof: bool = True
    dfof_percentile: float = 8.0
    enable_zscore: bool = True
    enable_smooth: bool = True
    smoothing_sigma: float = 2.0
    buffer_ms: int = 0
    min_trials: int = 3


class PlotData(BaseModel):
    title: str
    time: list[float]
    mean: list[float]
    sem: list[float]


class ComputeResponse(BaseModel):
    plots: list[PlotData]
    y_range: list[float]
    event_label: str


@router.post("/compute", response_model=ComputeResponse)
def compute(req: ComputeRequest) -> ComputeResponse:
    """Compute PETH plots based on the analysis configuration."""
    store = get_store()

    if not store.all_wrappers or not req.event_label:
        return ComputeResponse(plots=[], y_range=[0, 1], event_label=req.event_label)

    # Build pipeline from the first wrapper.
    ref_wrapper = store.all_wrappers[0]
    pipeline = ref_wrapper.build_pipeline(
        dfof_percentile=req.dfof_percentile,
        enable_dfof=req.enable_dfof,
        enable_zscore=req.enable_zscore,
        enable_smooth=req.enable_smooth,
        smoothing_sigma=req.smoothing_sigma,
    )

    # Resolve event code from label.
    event_code = ref_wrapper.get_event_code_for_label(req.event_label)

    # Gather plot data by view level.
    plots: list[PlotData] = []

    if req.view_level == "Population":
        for pop_name, samples in store.hierarchy.items():
            wrappers = []
            for ws in samples.values():
                wrappers.extend(ws)
            if not wrappers:
                continue
            try:
                result = compute_population_peth(
                    sessions=wrappers,
                    event_id=event_code,
                    pre_event_s=req.pre_event_s,
                    post_event_s=req.post_event_s,
                    pipeline=pipeline,
                    buffer_ms=req.buffer_ms,
                    min_trials=req.min_trials,
                )
                plots.append(PlotData(
                    title=f"{pop_name} (n={result.total_neurons})",
                    time=result.time_axis.tolist(),
                    mean=result.grand_mean.tolist(),
                    sem=result.grand_sem.tolist(),
                ))
            except Exception as exc:
                logger.warning("Population %s failed: %s", pop_name, exc)

    elif req.view_level == "Sample":
        for pop_name, samples in store.hierarchy.items():
            for sample_name, wrappers in samples.items():
                if not wrappers:
                    continue
                try:
                    result = compute_population_peth(
                        sessions=wrappers,
                        event_id=event_code,
                        pre_event_s=req.pre_event_s,
                        post_event_s=req.post_event_s,
                        pipeline=pipeline,
                        buffer_ms=req.buffer_ms,
                        min_trials=req.min_trials,
                    )
                    label = f"{pop_name}/{sample_name}" if pop_name != "default" else sample_name
                    plots.append(PlotData(
                        title=f"{label} (n={result.total_neurons})",
                        time=result.time_axis.tolist(),
                        mean=result.grand_mean.tolist(),
                        sem=result.grand_sem.tolist(),
                    ))
                except Exception as exc:
                    logger.warning("Sample %s/%s failed: %s", pop_name, sample_name, exc)

    elif req.view_level == "FOV":
        for pop_name, samples in store.hierarchy.items():
            for sample_name, wrappers in samples.items():
                for wrapper in wrappers:
                    try:
                        peth = compute_peth(
                            session=wrapper,
                            event_id=event_code,
                            pre_event_s=req.pre_event_s,
                            post_event_s=req.post_event_s,
                            pipeline=pipeline,
                            buffer_ms=req.buffer_ms,
                            min_trials=req.min_trials,
                        )
                        mean_trace = np.nanmean(peth.mean, axis=0)
                        sem_trace = np.nanmean(peth.sem, axis=0)
                        n_neurons = peth.mean.shape[0]
                        plots.append(PlotData(
                            title=f"{wrapper.name} (n={n_neurons})",
                            time=peth.time_axis.tolist(),
                            mean=mean_trace.tolist(),
                            sem=sem_trace.tolist(),
                        ))
                    except Exception as exc:
                        logger.warning("FOV %s failed: %s", wrapper.name, exc)

    # Compute shared y-range.
    if plots:
        all_means = [np.array(p.mean) for p in plots]
        all_sems = [np.array(p.sem) for p in plots]
        global_ymin = float(min((m - s).min() for m, s in zip(all_means, all_sems)))
        global_ymax = float(max((m + s).max() for m, s in zip(all_means, all_sems)))
        margin = (global_ymax - global_ymin) * 0.05
        y_range = [global_ymin - margin, global_ymax + margin]
    else:
        y_range = [0.0, 1.0]

    return ComputeResponse(plots=plots, y_range=y_range, event_label=req.event_label)
