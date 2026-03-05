"""FastAPI application -- entry point for Axplorer."""

from __future__ import annotations

import webbrowser
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.routers import upload, analysis, export

app = FastAPI(title="Axplorer", version="0.1.0")

app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(export.router)

# Serve the built React frontend from web/dist if it exists.
_dist = Path(__file__).resolve().parent.parent / "web" / "dist"
if _dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="frontend")


def main() -> None:
    """CLI entry point -- serve the FastAPI app."""
    import uvicorn

    webbrowser.open("http://localhost:8050")
    uvicorn.run("api.app:app", host="0.0.0.0", port=8050, reload=False)


if __name__ == "__main__":
    main()
