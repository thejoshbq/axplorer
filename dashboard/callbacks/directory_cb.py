"""Directory scan callbacks — mode toggle, directory walking, and session loading.

Handles the directory-based ingestion workflow:
    1. User toggles to "Directory" mode.
    2. User enters a directory path and clicks "Scan".
    3. Sessions populate a DataTable for selection.
    4. User selects a row and clicks "Load Selected" (single session) or
       "Load Population" (all selected sessions).
    5. The session is loaded into the same stores as the upload workflow,
       so all downstream callbacks work unchanged.
"""

from __future__ import annotations

from pathlib import Path

from dash import Input, Output, State, no_update

from axplorer.alignment.session import SessionWrapper
from axplorer.ingestion.discovery import discover_sessions
from axplorer.ingestion.loader import LoadError, load_session_files
from axplorer.types import SessionMeta
from dashboard import state as session_store


def register_directory_callbacks(app):
    """Register directory scan and session selection callbacks on *app*."""

    # ------------------------------------------------------------------
    # Callback 1: Toggle upload mode visibility
    # ------------------------------------------------------------------
    @app.callback(
        Output("div-file-pair-upload", "style"),
        Output("div-directory-upload", "style"),
        Input("radio-upload-mode", "value"),
    )
    def _toggle_upload_mode(mode):
        if mode == "directory":
            return {"display": "none"}, {"display": "block"}
        return {"display": "block"}, {"display": "none"}

    # ------------------------------------------------------------------
    # Callback 2: Scan directory
    # ------------------------------------------------------------------
    @app.callback(
        Output("dataset-sessions", "data"),
        Output("table-sessions", "data"),
        Output("dir-scan-status", "children"),
        Input("btn-scan-dir", "n_clicks"),
        State("input-dir-path", "value"),
        prevent_initial_call=True,
    )
    def _scan_directory(n_clicks, dir_path):
        if not dir_path or not dir_path.strip():
            return no_update, no_update, "Please enter a directory path."

        try:
            metas = discover_sessions(dir_path.strip())
        except ValueError as exc:
            return no_update, no_update, str(exc)
        except Exception as exc:
            return no_update, no_update, f"Scan error: {exc}"

        if not metas:
            return [], [], "No valid sessions found."

        # Serialize SessionMeta list to JSON-safe dicts (paths as strings).
        session_dicts = [
            {
                "phase": m.phase,
                "animal_id": m.animal_id,
                "sex": m.sex,
                "fov": m.fov,
                "is_tracked": m.is_tracked,
                "npy_path": str(m.npy_path),
                "mat_path": str(m.mat_path),
            }
            for m in metas
        ]

        # Build table rows with file sizes.
        table_rows = []
        for m in metas:
            npy_mb = m.npy_path.stat().st_size / (1024 * 1024) if m.npy_path.exists() else 0.0
            mat_mb = m.mat_path.stat().st_size / (1024 * 1024) if m.mat_path.exists() else 0.0
            table_rows.append({
                "phase": m.phase,
                "animal_id": m.animal_id,
                "sex": m.sex,
                "fov": m.fov,
                "is_tracked": str(m.is_tracked),
                "npy_size_mb": f"{npy_mb:.2f}",
                "mat_size_mb": f"{mat_mb:.2f}",
            })

        status_msg = f"Found {len(metas)} session(s)."
        return session_dicts, table_rows, status_msg

    # ------------------------------------------------------------------
    # Callback 3: Select All toggle
    # ------------------------------------------------------------------
    @app.callback(
        Output("table-sessions", "selected_rows"),
        Input("chk-select-all", "value"),
        State("table-sessions", "data"),
        prevent_initial_call=True,
    )
    def _toggle_select_all(select_all, table_data):
        if select_all and table_data:
            return list(range(len(table_data)))
        return []

    # ------------------------------------------------------------------
    # Callback 4: Enable/disable "Load Selected" and "Load Population"
    # ------------------------------------------------------------------
    @app.callback(
        Output("btn-load-selected", "disabled"),
        Output("btn-load-population", "disabled"),
        Input("table-sessions", "selected_rows"),
    )
    def _toggle_load_buttons(selected):
        disabled = not selected
        return disabled, disabled

    # ------------------------------------------------------------------
    # Callback 5: Load selected session (single)
    # ------------------------------------------------------------------
    @app.callback(
        Output("session-token", "data", allow_duplicate=True),
        Output("session-metadata", "data", allow_duplicate=True),
        Output("dir-scan-status", "children", allow_duplicate=True),
        Output("dropdown-event", "options", allow_duplicate=True),
        Output("dropdown-event", "value", allow_duplicate=True),
        Output("dropdown-cells", "options", allow_duplicate=True),
        Input("btn-load-selected", "n_clicks"),
        State("table-sessions", "selected_rows"),
        State("dataset-sessions", "data"),
        State("input-fps", "value"),
        State("input-frame-avg", "value"),
        State("dropdown-task-type", "value"),
        prevent_initial_call=True,
    )
    def _load_selected_session(
        n_clicks,
        selected_rows,
        session_dicts,
        fps,
        frame_avg,
        task_type,
    ):
        if not selected_rows or not session_dicts:
            return (
                no_update, no_update, "No session selected.",
                no_update, no_update, no_update,
            )

        row_idx = selected_rows[0]
        if row_idx >= len(session_dicts):
            return (
                no_update, no_update, "Invalid selection.",
                no_update, no_update, no_update,
            )

        sd = session_dicts[row_idx]

        # Parse parameters.
        try:
            fps_val = float(fps) if fps else 30.0
            frame_avg_val = int(frame_avg) if frame_avg else 4
        except (TypeError, ValueError):
            return (
                no_update, no_update, "Invalid FPS or Frame Avg value.",
                no_update, no_update, no_update,
            )

        resolved_task = task_type if task_type != "auto" else None

        # Reconstruct paths and load.
        npy_path = Path(sd["npy_path"])
        mat_path = Path(sd["mat_path"])

        try:
            sample, metadata = load_session_files(
                signal_path=npy_path,
                event_path=mat_path,
                fps=fps_val,
                frame_averaging=frame_avg_val,
                task_type=resolved_task,
                session_name=npy_path.stem,
            )
        except LoadError as exc:
            return (
                no_update, no_update,
                f"Load failed: {'; '.join(exc.errors)}",
                no_update, no_update, no_update,
            )
        except Exception as exc:
            return (
                no_update, no_update, f"Unexpected error: {exc}",
                no_update, no_update, no_update,
            )

        # Wrap and store.
        wrapper = SessionWrapper(sample)
        token = session_store.create_session(wrapper)

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

        event_options = [
            {"label": lbl, "value": lbl} for lbl in wrapper.get_event_labels()
        ]
        default_event = event_options[0]["value"] if event_options else None

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

    # ------------------------------------------------------------------
    # Callback 6: Load Population (all selected sessions)
    # ------------------------------------------------------------------
    @app.callback(
        Output("population-token", "data"),
        Output("dir-scan-status", "children", allow_duplicate=True),
        Output("dropdown-event", "options", allow_duplicate=True),
        Output("dropdown-event", "value", allow_duplicate=True),
        Output("dropdown-cells", "options", allow_duplicate=True),
        Input("btn-load-population", "n_clicks"),
        State("table-sessions", "selected_rows"),
        State("dataset-sessions", "data"),
        State("input-fps", "value"),
        State("input-frame-avg", "value"),
        State("dropdown-task-type", "value"),
        prevent_initial_call=True,
    )
    def _load_population(
        n_clicks,
        selected_rows,
        session_dicts,
        fps,
        frame_avg,
        task_type,
    ):
        if not selected_rows or not session_dicts:
            return (
                no_update, "No sessions selected.",
                no_update, no_update, no_update,
            )

        # Parse parameters.
        try:
            fps_val = float(fps) if fps else 30.0
            frame_avg_val = int(frame_avg) if frame_avg else 4
        except (TypeError, ValueError):
            return (
                no_update, "Invalid FPS or Frame Avg value.",
                no_update, no_update, no_update,
            )

        resolved_task = task_type if task_type != "auto" else None

        # Load all selected sessions.
        entries = []
        failed = []
        all_event_labels = set()
        total_neurons = 0

        for row_idx in selected_rows:
            if row_idx >= len(session_dicts):
                continue

            sd = session_dicts[row_idx]
            npy_path = Path(sd["npy_path"])
            mat_path = Path(sd["mat_path"])
            session_name = npy_path.stem

            try:
                sample, metadata = load_session_files(
                    signal_path=npy_path,
                    event_path=mat_path,
                    fps=fps_val,
                    frame_averaging=frame_avg_val,
                    task_type=resolved_task,
                    session_name=session_name,
                )
            except (LoadError, Exception) as exc:
                err_msg = '; '.join(exc.errors) if isinstance(exc, LoadError) else str(exc)
                failed.append(f"{session_name}: {err_msg}")
                continue

            wrapper = SessionWrapper(sample)
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
            entries.append((wrapper, meta_dict))
            all_event_labels.update(wrapper.get_event_labels())
            total_neurons += metadata.n_neurons

        if not entries:
            fail_detail = "; ".join(failed) if failed else "Unknown error"
            return (
                no_update, f"All sessions failed to load: {fail_detail}",
                no_update, no_update, no_update,
            )

        # Store population.
        pop_token = session_store.create_population(entries)

        # Build union of event labels across all sessions.
        event_options = [
            {"label": lbl, "value": lbl}
            for lbl in sorted(all_event_labels)
        ]
        default_event = event_options[0]["value"] if event_options else None

        # Build cell options covering all neurons across all sessions.
        cell_options = [
            {"label": f"Cell {i}", "value": i}
            for i in range(total_neurons)
        ]

        # Status message.
        status_parts = [
            f"Population loaded: {len(entries)} session(s), "
            f"{total_neurons} total neurons"
        ]
        if failed:
            status_parts.append(f" ({len(failed)} failed: {'; '.join(failed)})")

        return pop_token, "".join(status_parts), event_options, default_event, cell_options


__all__ = ["register_directory_callbacks"]
