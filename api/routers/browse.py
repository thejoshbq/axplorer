"""Browse router -- server-side filesystem navigation."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["browse"])

_HOME = Path.home()

_TYPE_MAP = {
    ".duckdb": "duckdb",
    ".npy": "npy",
    ".mat": "mat",
    ".xlsx": "xlsx",
}


class BrowseEntry(BaseModel):
    name: str
    path: str
    type: str  # "dir" | "duckdb" | "npy" | "mat" | "xlsx" | "file"
    size: int | None = None


class BrowseResponse(BaseModel):
    current: str
    parent: str | None
    entries: list[BrowseEntry]


@router.get("/browse", response_model=BrowseResponse)
def browse(path: str = "~") -> BrowseResponse:
    """List directory contents, restricted to home directory."""
    target = Path(path).expanduser().resolve()

    if not target.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a directory: {target}")

    # Security: restrict to home directory tree.
    try:
        target.relative_to(_HOME)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Access restricted to home directory",
        )

    parent = str(target.parent) if target != _HOME else None

    dirs: list[BrowseEntry] = []
    files: list[BrowseEntry] = []

    try:
        for entry in sorted(target.iterdir(), key=lambda e: e.name.lower()):
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                dirs.append(BrowseEntry(name=entry.name, path=str(entry), type="dir"))
            elif entry.is_file():
                ext = entry.suffix.lower()
                ftype = _TYPE_MAP.get(ext, "file")
                files.append(
                    BrowseEntry(
                        name=entry.name,
                        path=str(entry),
                        type=ftype,
                        size=entry.stat().st_size,
                    )
                )
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied: {target}")

    return BrowseResponse(
        current=str(target),
        parent=parent,
        entries=dirs + files,
    )
