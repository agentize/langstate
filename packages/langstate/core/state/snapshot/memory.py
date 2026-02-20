from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional, TypeVar

from core.state.base.base import BaseDAHState
from core.state.snapshot.base import BaseSnapshotStore
from core.state.snapshot.schema import Snapshot

TState = TypeVar("TState", bound=BaseDAHState[Any])


class InMemorySnapshotStore(BaseSnapshotStore[TState]):
    """In-memory implementation of snapshot storage.

    Stores snapshots in a list with bounded capacity.
    When max_snapshots is reached, oldest snapshots are discarded (FIFO).

    Thread-safety: Not thread-safe. Use appropriate synchronization
    if accessing from multiple coroutines concurrently.
    """

    DEFAULT_MAX_SNAPSHOTS = 100

    def __init__(self, max_snapshots: int = DEFAULT_MAX_SNAPSHOTS) -> None:
        """Initialize the in-memory snapshot store.

        Args:
            max_snapshots: Maximum number of snapshots to retain.
                When exceeded, oldest snapshots are removed.
                Defaults to 100.
        """
        self._snapshots: List[Snapshot[TState]] = []
        self._max_snapshots = max_snapshots
        self._total_recorded = 0  # Track total for index assignment

    async def record_snapshot(
        self,
        mutator_id: str,
        state: TState,
    ) -> None:
        """Record a snapshot for a mutator run.

        Creates a deep copy of the state using state.copy() to ensure
        graph-safe copying without mutation side effects.

        Args:
            mutator_id: Identifier of the mutator that produced this state
            state: The state to snapshot (will be deep copied)
        """
        # Deep copy the state to prevent mutation
        state_copy = state.copy()

        snapshot: Snapshot[TState] = Snapshot(
            mutator_id=mutator_id,
            timestamp=datetime.now(timezone.utc),
            state=state_copy,  # type: ignore[arg-type]
            index=self._total_recorded,
        )

        self._snapshots.append(snapshot)
        self._total_recorded += 1

        # Enforce bounded storage - remove oldest if over limit
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots.pop(0)

    async def get_snapshots(self) -> List[Snapshot[TState]]:
        """Return all recorded snapshots.

        Returns:
            List of Snapshot objects in chronological order
        """
        return list(self._snapshots)

    async def get_snapshots_by_mutator(self, mutator_id: str) -> List[Snapshot[TState]]:
        """Return snapshots filtered by mutator ID.

        Args:
            mutator_id: The mutator identifier to filter by

        Returns:
            List of Snapshot objects from the specified mutator
        """
        return [s for s in self._snapshots if s.mutator_id == mutator_id]

    async def get_latest(self) -> Optional[Snapshot[TState]]:
        """Return the most recent snapshot.

        Returns:
            The latest Snapshot or None if no snapshots exist
        """
        if not self._snapshots:
            return None
        return self._snapshots[-1]

    async def clear(self) -> None:
        """Clear all stored snapshots."""
        self._snapshots.clear()
        self._total_recorded = 0

    async def count(self) -> int:
        """Return the number of stored snapshots.

        Returns:
            Number of snapshots currently stored
        """
        return len(self._snapshots)

    @property
    def max_snapshots(self) -> int:
        """Get the maximum number of snapshots allowed."""
        return self._max_snapshots
