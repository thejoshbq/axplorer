"""Ingestion layer — file validation, session loading, and directory discovery."""

from axplorer.ingestion.validators import (
    ValidationResult,
    validate_signal_file,
    validate_event_file,
    detect_task_type,
    validate_alignment,
)
from axplorer.ingestion.loader import load_session_files, LoadError
from axplorer.ingestion.discovery import discover_sessions, parse_animal_sex

__all__ = [
    "ValidationResult",
    "validate_signal_file",
    "validate_event_file",
    "detect_task_type",
    "validate_alignment",
    "load_session_files",
    "LoadError",
    "discover_sessions",
    "parse_animal_sex",
]
