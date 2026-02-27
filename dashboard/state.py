"""Server-side session state --- maps UUID tokens to SessionWrapper objects.

Provides a thread-safe in-memory store keyed by UUID strings.  Each entry
holds a ``SessionWrapper`` (or any object) that persists for the lifetime
of a browser session.
"""

from __future__ import annotations

import threading
import uuid
from typing import Optional


_store: dict[str, object] = {}
_lock = threading.Lock()


def create_session(wrapper: object) -> str:
    """Store *wrapper* and return a new UUID token.

    Args:
        wrapper: The SessionWrapper (or any object) to store.

    Returns:
        A UUID-4 string that acts as the session key.
    """
    token = uuid.uuid4().hex
    with _lock:
        _store[token] = wrapper
    return token


def get_session(token: str) -> Optional[object]:
    """Retrieve the object associated with *token*.

    Args:
        token: UUID string returned by :func:`create_session`.

    Returns:
        The stored object, or ``None`` if the token is unknown.
    """
    with _lock:
        return _store.get(token)


def create_population(entries: list[tuple[object, dict]]) -> str:
    """Store a list of (SessionWrapper, meta_dict) pairs; return UUID token.

    Args:
        entries: List of ``(SessionWrapper, meta_dict)`` tuples where
            *meta_dict* preserves session identity for labeling.

    Returns:
        A UUID-4 string that acts as the population key.
    """
    token = uuid.uuid4().hex
    with _lock:
        _store[token] = entries
    return token


def get_population(token: str) -> list[tuple[object, dict]] | None:
    """Retrieve the population list for the given token.

    Args:
        token: UUID string returned by :func:`create_population`.

    Returns:
        The stored list, or ``None`` if the token is unknown.
    """
    with _lock:
        return _store.get(token)


def delete_session(token: str) -> bool:
    """Remove the entry for *token*.

    Args:
        token: UUID string to delete.

    Returns:
        ``True`` if the token existed and was deleted, ``False`` otherwise.
    """
    with _lock:
        if token in _store:
            del _store[token]
            return True
        return False


__all__ = [
    "create_session",
    "get_session",
    "delete_session",
    "create_population",
    "get_population",
]
