from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..schema import InterpretiveState


class SnapshotStore(ABC):
    """Interface for storing snapshots of an State.

    Implementations can store snapshots in-memory, on-disk, or in a database.
    """

    @abstractmethod
    def record_snapshot(
        self,
        mutator_id: str,
        state: InterpretiveState,
    ) -> None:
        """Record a snapshot for a mutator run.

        Implementations may choose to construct a `Snapshot` instance or store
        raw dicts. Timestamping is the implementor's responsibility.
        """

    @abstractmethod
    def get_snapshots(self) -> List[InterpretiveState]:
        """Return list of recorded snapshots as dictionaries."""

    @abstractmethod
    def clear(self) -> None:
        """Clear stored snapshots (useful for tests or bounded stores)."""
