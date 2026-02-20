from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, List, Optional, TypeVar

if TYPE_CHECKING:
    from core.state.snapshot.schema import Snapshot

from core.state.base.base import BaseDAHState

TState = TypeVar("TState", bound=BaseDAHState[Any])


class BaseSnapshotStore(ABC, Generic[TState]):
    """Interface for storing snapshots of a State.

    Snapshots are deep copies of state at specific points in time,
    typically recorded after each mutator run. This enables:
    - Audit trails of state changes
    - Debugging by inspecting historical states
    - Potential undo/restore functionality

    Implementations can store snapshots in-memory, on-disk, or in a database.
    States are graphs (DAH-based), so implementations must use state.copy()
    to avoid mutation side effects.
    """

    @abstractmethod
    async def record_snapshot(
        self,
        mutator_id: str,
        state: TState,
    ) -> None:
        """Record a snapshot for a mutator run.

        Creates a deep copy of the state to prevent mutation.
        Timestamping is handled automatically.

        Args:
            mutator_id: Identifier of the mutator that produced this state
            state: The state to snapshot (will be deep copied)
        """

    @abstractmethod
    async def get_snapshots(self) -> List["Snapshot[TState]"]:
        """Return all recorded snapshots.

        Returns:
            List of Snapshot objects containing state copies and metadata
        """

    @abstractmethod
    async def get_snapshots_by_mutator(
        self, mutator_id: str
    ) -> List["Snapshot[TState]"]:
        """Return snapshots filtered by mutator ID.

        Args:
            mutator_id: The mutator identifier to filter by

        Returns:
            List of Snapshot objects from the specified mutator
        """

    @abstractmethod
    async def get_latest(self) -> Optional["Snapshot[TState]"]:
        """Return the most recent snapshot.

        Returns:
            The latest Snapshot or None if no snapshots exist
        """

    @abstractmethod
    async def clear(self) -> None:
        """Clear all stored snapshots."""

    @abstractmethod
    async def count(self) -> int:
        """Return the number of stored snapshots.

        Returns:
            Number of snapshots currently stored
        """
