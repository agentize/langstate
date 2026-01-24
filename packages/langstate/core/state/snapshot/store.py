from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, List

from packages.langstate.core.typing.generic import TFieldData


class SnapshotStore(ABC, Generic[TFieldData]):
    """Interface for storing snapshots of an State.

    Implementations can store snapshots in-memory, on-disk, or in a database.
    """

    @abstractmethod
    def record_snapshot(
        self,
        mutator_id: str,
        state: TFieldData,
    ) -> None:
        """Record a snapshot for a mutator run.

        Implementations may choose to construct a `Snapshot` instance or store
        raw dicts. Timestamping is the implementor's responsibility.
        """

    @abstractmethod
    def get_snapshots(self) -> List[TFieldData]:
        """Return list of recorded snapshots as dictionaries."""

    @abstractmethod
    def clear(self) -> None:
        """Clear stored snapshots (useful for tests or bounded stores)."""
