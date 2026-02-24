"""Repository module.

This module provides the Repository interface and implementations
for managing state persistence and retrieval following the Repository pattern.
"""

from .base import BaseRepository
from .snapshot_repository import (
    BaseSnapshotRepository,
    HistoryFilter,
    InMemorySnapshotRepository,
)

__all__ = [
    "BaseRepository",
    "BaseSnapshotRepository",
    "HistoryFilter",
    "InMemorySnapshotRepository",
]
