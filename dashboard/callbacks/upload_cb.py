"""Upload callbacks — file validation + session loading.

Handles the upload-to-load workflow:
    1. User drops .npy + .xlsx files into the upload zones.
    2. User configures FPS, frame_avg, task type.
    3. Clicking "Load Session" validates, constructs the Sample, stores the
       SessionWrapper, and populates downstream controls.
"""

from __future__ import annotations

import base64
import json
import tempfile
from pathlib import Path

import numpy as np
from dash import Input, Output, State, callback_context, no_update

from dashboard import state as session_store
from axplorer.alignment.session import SessionWrapper
from axplorer.ingestion.loader import LoadError, load_session_files


def register_upload_callbacks(app):
    """Register all upload-related callbacks on *app*."""

    # ------------------------------------------------------------------
    # Upload status feedback (lightweight — just shows filenames)
    # ------------------------------------------------------------------
    @app.callback(
        Output("upload-status", "children"),
        Input("upload-signal", "filename"),
        Input("upload-events", "filename"),
    )
    def _show_upload_filenames(sig_name, evt_name):
        parts = []
        if sig_name:
            parts.append(f"Signal: {sig_name}")
        if evt_name:
            parts.append(f"Events: {evt_name}")
        return " | ".join(parts) if parts else ""

    # ------------------------------------------------------------------
    # Load Session button
    # ------------------------------------------------------------------
    @app.callback(
        Output("session-token", "data"),
        Output("session-metadata", "data"),
        Output("upload-status", "children", allow_duplicate=True),
        Output("dropdown-event", "options"),
        Output("dropdown-event", "value"),
        Output("dropdown-cells", "options"),
        Input("btn-load-session", "n_clicks"),
        State("upload-signal", "contents"),
        State("upload-signal", "filename"),
        State("upload-events", "contents"),
        State("upload-events", "filename"),
        State("input-fps", "value"),
        State("input-frame-avg", "value"),
        State("dropdown-task-type", "value"),
        prevent_initial_call=True,
    )
    def _load_session(
        n_clicks,
        sig_contents,
        sig_filename,
        evt_contents,
        evt_filename,
        fps,
        frame_avg,
        task_type,
    ):
        if not sig_contents or not evt_contents:
            return (
                no_update,
                no_update,
                "Please upload both a signal (.npy) and event (.xlsx/.mat) file.",
                no_update,
                no_update,
                no_update,
            )

        try:
            fps = float(fps) if fps else 30.0
            frame_avg = int(frame_avg) if frame_avg else 4
        except (TypeError, ValueError):
            return (
                no_update,
                no_update,
                "Invalid FPS or Frame Avg value.",
                no_update,
                no_update,
                no_update,
            )

        # Decode base64 uploads and write to temp files.
        try:
            sig_path = _decode_to_tempfile(sig_contents, sig_filename)
            evt_path = _decode_to_tempfile(evt_contents, evt_filename)
        except Exception as exc:
            return (
                no_update,
                no_update,
                f"File decode error: {exc}",
                no_update,
                no_update,
                no_update,
            )

        # Resolve task type.
        resolved_task = task_type if task_type != "auto" else None

        # Load session.
        try:
            sample, metadata = load_session_files(
                signal_path=sig_path,
                event_path=evt_path,
                fps=fps,
                frame_averaging=frame_avg,
                task_type=resolved_task,
                session_name=Path(sig_filename).stem if sig_filename else None,
            )
        except LoadError as exc:
            return (
                no_update,
                no_update,
                f"Load failed: {'; '.join(exc.errors)}",
                no_update,
                no_update,
                no_update,
            )
        except Exception as exc:
            return (
                no_update,
                no_update,
                f"Unexpected error: {exc}",
                no_update,
                no_update,
                no_update,
            )

        # Wrap and store.
        wrapper = SessionWrapper(sample)
        token = session_store.create_session(wrapper)

        # Serialize metadata for the dcc.Store (must be JSON-serialisable).
        meta_dict = {
            "name": metadata.name,
            "n_neurons": metadata.n_neurons,
            "n_frames": metadata.n_frames,
            "n_events": metadata.n_events,
            "event_counts": metadata.event_counts,
            "effective_fps": metadata.effective_fps,
            "duration_s": metadata.duration_s,
            "task_type": metadata.task_type,
        }

        # Populate event dropdown.
        event_options = [
            {"label": lbl, "value": lbl} for lbl in wrapper.get_event_labels()
        ]
        default_event = event_options[0]["value"] if event_options else None

        # Populate cell selector.
        cell_options = [
            {"label": f"Cell {i}", "value": i}
            for i in range(metadata.n_neurons)
        ]

        status_msg = (
            f"Loaded: {metadata.name} — "
            f"{metadata.n_neurons} neurons, "
            f"{metadata.n_events} events, "
            f"{metadata.duration_s:.1f}s"
        )

        return token, meta_dict, status_msg, event_options, default_event, cell_options


def _decode_to_tempfile(contents: str, filename: str) -> Path:
    """Decode a Dash upload (base64) and write to a named temp file.

    Args:
        contents: The base64-encoded file string from ``dcc.Upload``.
        filename: Original filename used for the temp-file suffix.

    Returns:
        Path to the temporary file.
    """
    _, content_string = contents.split(",", 1)
    decoded = base64.b64decode(content_string)

    suffix = Path(filename).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(decoded)
    tmp.flush()
    tmp.close()
    return Path(tmp.name)
