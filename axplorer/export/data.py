"""Data export utilities --- CSV and HDF5."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from axplorer.types import PETHResult, SessionMetadata


def export_peth_csv(
    peth: PETHResult,
    path: str | Path | None = None,
) -> str | None:
    """Export PETH mean +/- SEM to CSV.

    Creates a CSV with columns:
    ``time, cell_0_mean, cell_0_sem, cell_1_mean, cell_1_sem, ...``

    Args:
        peth: PETHResult to export.
        path: Output file path. If None, returns the CSV as a string.

    Returns:
        CSV string when *path* is None, otherwise None (writes to file).
    """
    n_neurons = peth.mean.shape[0]

    columns: dict[str, np.ndarray] = {"time": peth.time_axis}
    for i in range(n_neurons):
        columns[f"cell_{i}_mean"] = peth.mean[i]
        columns[f"cell_{i}_sem"] = peth.sem[i]

    df = pd.DataFrame(columns)

    if path is None:
        return df.to_csv(index=False)

    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest, index=False)
    return None


def export_session_hdf5(
    metadata: SessionMetadata,
    peth_results: dict[str, PETHResult],
    path: str | Path | None = None,
) -> bytes | None:
    """Export session analysis results to HDF5.

    File structure::

        /metadata          (attrs: name, n_neurons, n_frames, ...)
        /events/<label>/mean        (neurons x time)
        /events/<label>/sem         (neurons x time)
        /events/<label>/windows     (trials x neurons x time)
        /events/<label>/time_axis   (time,)

    Args:
        metadata: Session metadata.
        peth_results: Mapping of event labels to PETHResult objects.
        path: Output file path. If None, returns raw bytes via an
            in-memory buffer.

    Returns:
        HDF5 bytes when *path* is None, otherwise None (writes to file).
    """
    if path is not None:
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        _write_hdf5(dest, metadata, peth_results)
        return None

    buf = BytesIO()
    _write_hdf5(buf, metadata, peth_results)
    return buf.getvalue()


def _write_hdf5(
    target: Path | BytesIO,
    metadata: SessionMetadata,
    peth_results: dict[str, PETHResult],
) -> None:
    """Write session data into an HDF5 file or buffer.

    Args:
        target: File path or BytesIO buffer.
        metadata: Session metadata stored as root-group attributes.
        peth_results: Event-keyed PETH data written under ``/events``.
    """
    with h5py.File(target, "w") as f:
        # -- metadata as root-group attributes --
        meta_grp = f.create_group("metadata")
        meta_grp.attrs["name"] = metadata.name
        meta_grp.attrs["n_neurons"] = metadata.n_neurons
        meta_grp.attrs["n_frames"] = metadata.n_frames
        meta_grp.attrs["n_events"] = metadata.n_events
        meta_grp.attrs["effective_fps"] = metadata.effective_fps
        meta_grp.attrs["duration_s"] = metadata.duration_s
        meta_grp.attrs["task_type"] = metadata.task_type

        # event_counts stored as individual attributes under a sub-group
        ec_grp = meta_grp.create_group("event_counts")
        for label, count in metadata.event_counts.items():
            ec_grp.attrs[label] = count

        # -- per-event PETH datasets --
        events_grp = f.create_group("events")
        for label, peth in peth_results.items():
            grp = events_grp.create_group(label)
            grp.create_dataset("mean", data=np.asarray(peth.mean))
            grp.create_dataset("sem", data=np.asarray(peth.sem))
            grp.create_dataset("windows", data=np.asarray(peth.event_windows))
            grp.create_dataset("time_axis", data=np.asarray(peth.time_axis))
            grp.attrs["event_label"] = peth.event_label
            grp.attrs["n_trials"] = peth.n_trials
            grp.attrs["pre_event_s"] = peth.pre_event_s
            grp.attrs["post_event_s"] = peth.post_event_s
