"""Base Snapshot Repository interface.

Extends BaseRepository with snapshot-specific operations for version history,
delta/keyframe storage, and time-travel capabilities.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Generic, List, Optional, TypeVar

from core.state.base.base import BaseDAHState
from core.state.repository.base import BaseRepository
from core.state.snapshot.snapshot import Snapshot
from .schema import HistoryFilter  # noqa: F401

TState = TypeVar("TState", bound=BaseDAHState[Any])


class BaseSnapshotRepository(BaseRepository[TState], Generic[TState]):
    """Repository with snapshot version history.

    Extends BaseRepository with methods for appending snapshots,
    retrieving the latest version, checking out (reverting to) a
    specific version, and listing history with filters.

    Snapshots are stored as a mix of keyframes (full copies) and
    deltas (differences from the previous snapshot). The keyframe
    interval is implementation-defined.

    Implementations must handle transparent reconstruction of full
    state from delta chains when returning Snapshot objects.
    """

    @abstractmethod
    async def append(self, state_id: str, snapshot: Snapshot[TState]) -> None:
        """Append a new snapshot (keyframe or delta).

        The implementation decides whether to store as a delta or
        keyframe based on the configured interval.

        Args:
            state_id: Unique identifier for the state timeline
            snapshot: The snapshot to append
        """

    @abstractmethod
    async def get_latest(self, state_id: str) -> Optional[Snapshot[TState]]:
        """Get the most recent snapshot, fully reconstructed.

        Args:
            state_id: Unique identifier for the state timeline

        Returns:
            The latest Snapshot with full state, or None if empty
        """

    @abstractmethod
    async def checkout(self, state_id: str, version: int) -> Optional[Snapshot[TState]]:
        """Revert to a specific version.

        All versions above ``version`` are permanently deleted.

        Args:
            state_id: Unique identifier for the state timeline
            version: The version index to revert to

        Returns:
            The Snapshot at the given version, or None if not found
        """

    @abstractmethod
    async def list_history(
        self, state_id: str, history_filter: HistoryFilter
    ) -> List[Snapshot[TState]]:
        """List snapshots matching the given filter.

        Returned snapshots are fully reconstructed (not raw deltas).

        Args:
            state_id: Unique identifier for the state timeline
            history_filter: Criteria to filter by version range and/or time

        Returns:
            List of matching Snapshot objects in chronological order
        """
