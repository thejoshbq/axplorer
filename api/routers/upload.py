"""Upload router -- load data and check status."""

from __future__ import annotations

import shutil
from pathlib import Path

from pydantic import BaseModel
from fastapi import APIRouter, File, HTTPException, UploadFile

from api.state import DataStore
from axplorer.ingestion.detection import classify_paths
from axplorer.ingestion.validators import list_h5_kinds

_UPLOAD_DIR = Path.home() / ".axplorer"

router = APIRouter(prefix="/api", tags=["upload"])

# Singleton store shared across routers.
store = DataStore()


def get_store() -> DataStore:
    """Return the singleton DataStore instance."""
    return store


class LoadRequest(BaseModel):
    source: str | None = None  # "filesystem" | "database"; auto-detected if omitted
    data_level: str | None = None  # auto-detected if omitted
    paths: list[str]
    db_path: str | None = None  # None → default ~/.pynapse/pynapse.duckdb
    h5_kind: str | None = None  # required when paths resolve to .h5 signal files


class DetectRequest(BaseModel):
    paths: list[str]


class DetectResponse(BaseModel):
    source: str
    data_level: str
    available_h5_kinds: list[str] = []


class LoadResponse(BaseModel):
    status: str
    available_events: list[str]
    fov_count: int
    population_count: int
    population_names: list[str]


class StatusResponse(BaseModel):
    status: str
    loading: bool
    available_events: list[str]
    fov_count: int
    population_count: int
    population_names: list[str]


@router.post("/detect", response_model=DetectResponse)
def detect_type(req: DetectRequest) -> DetectResponse:
    """Classify paths and return the detected source + data level.

    When any of the paths is (or a probed FOV directory contains) a roigbiv
    ``.h5`` trace export, also returns the trace kinds available in the
    first such file so the frontend can render a kind selector -- there is
    no default kind.
    """
    try:
        source, level = classify_paths(req.paths)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    available_h5_kinds: list[str] = []
    for p in req.paths:
        path = Path(p).expanduser().resolve()
        if path.is_file() and path.suffix.lower() in (".h5", ".hdf5"):
            available_h5_kinds = list_h5_kinds(path)
            break
        if path.is_dir():
            h5_files = sorted(path.rglob("*.h5"))
            if h5_files:
                available_h5_kinds = list_h5_kinds(h5_files[0])
                break

    return DetectResponse(
        source=source, data_level=level, available_h5_kinds=available_h5_kinds,
    )


@router.post("/load", response_model=LoadResponse)
def load_data(req: LoadRequest) -> LoadResponse:
    """Load data at the specified level from the given paths."""
    source = req.source
    data_level = req.data_level

    if source is None or data_level is None:
        try:
            detected_source, detected_level = classify_paths(req.paths)
            source = source or detected_source
            data_level = data_level or detected_level
        except ValueError:
            source = source or "filesystem"
            data_level = data_level or "Project"

    store.source = source
    store.db_path = req.db_path
    store.data_level = data_level
    store.data_paths = req.paths
    store.h5_kind = req.h5_kind
    store.load_data()
    return LoadResponse(
        status=store.status,
        available_events=store.available_events,
        fov_count=len(store.all_wrappers),
        population_count=len(store.hierarchy),
        population_names=store.population_names,
    )


@router.post("/db/upload")
async def upload_db_file(file: UploadFile = File(...)) -> dict:
    """Upload a .duckdb file and return its server-side path."""
    if not (file.filename or "").endswith(".duckdb"):
        raise HTTPException(status_code=400, detail="Only .duckdb files are accepted")
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = _UPLOAD_DIR / (file.filename or "upload.duckdb")
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"db_path": str(dest)}


@router.get("/status", response_model=StatusResponse)
def get_status() -> StatusResponse:
    """Return current data store status."""
    return StatusResponse(
        status=store.status,
        loading=store.loading,
        available_events=store.available_events,
        fov_count=len(store.all_wrappers),
        population_count=len(store.hierarchy),
        population_names=store.population_names,
    )
