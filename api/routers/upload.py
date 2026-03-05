"""Upload router -- load data and check status."""

from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter

from api.state import DataStore

router = APIRouter(prefix="/api", tags=["upload"])

# Singleton store shared across routers.
store = DataStore()


def get_store() -> DataStore:
    """Return the singleton DataStore instance."""
    return store


class LoadRequest(BaseModel):
    data_level: str
    paths: list[str]


class LoadResponse(BaseModel):
    status: str
    available_events: list[str]
    fov_count: int
    population_count: int


class StatusResponse(BaseModel):
    status: str
    loading: bool
    available_events: list[str]
    fov_count: int
    population_count: int


@router.post("/load", response_model=LoadResponse)
def load_data(req: LoadRequest) -> LoadResponse:
    """Load data at the specified level from the given paths."""
    store.data_level = req.data_level
    store.data_paths = req.paths
    store.load_data()
    return LoadResponse(
        status=store.status,
        available_events=store.available_events,
        fov_count=len(store.all_wrappers),
        population_count=len(store.hierarchy),
    )


@router.get("/status", response_model=StatusResponse)
def get_status() -> StatusResponse:
    """Return current data store status."""
    return StatusResponse(
        status=store.status,
        loading=store.loading,
        available_events=store.available_events,
        fov_count=len(store.all_wrappers),
        population_count=len(store.hierarchy),
    )
