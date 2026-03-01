"""In-memory Snapshot Repository with delta/keyframe compression.

Stores snapshots using a mix of keyframes (full state) and deltas
(JSON diffs from the previous entry). Keyframes are created every
``keyframe_interval`` versions for efficient reconstruction.
"""

from __future__ import annotations

import json
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    cast,
)

from core.state.base.base import BaseDAHState
from core.state.repository.snapshot_repository.base.base import BaseSnapshotRepository
from core.state.repository.snapshot_repository.base.schema import HistoryFilter
from core.state.snapshot.snapshot import Snapshot
from .schema import InternalEntry
from .utils import apply_delta, compute_delta

TState = TypeVar("TState", bound=BaseDAHState[Any])


class InMemorySnapshotRepository(BaseSnapshotRepository[TState], Generic[TState]):
    """In-memory snapshot repository backed by delta/keyframe compression.

    Constructor args:
        state_class: The concrete state class (e.g. ``State``) used to
            reconstruct snapshots from JSON via ``from_json()``.
        keyframe_interval: Store a full keyframe every *N* versions.
            Defaults to 10.
    """

    DEFAULT_KEYFRAME_INTERVAL = 10

    def __init__(
        self,
        state_class: Type[TState],
        keyframe_interval: int = DEFAULT_KEYFRAME_INTERVAL,
    ) -> None:
        self._state_class: Type[TState] = state_class
        self._keyframe_interval = keyframe_interval
        self._storage: Dict[str, List[InternalEntry]] = {}

    @property
    def keyframe_interval(self) -> int:
        """Return the configured keyframe interval."""
        return self._keyframe_interval

    async def append(self, state_id: str, snapshot: Snapshot[TState]) -> None:
        """Append a snapshot, storing it as keyframe or delta."""
        history = self._storage.setdefault(state_id, [])
        index = len(history)

        state_json_str = snapshot.state.to_json()
        state_json_dict: Dict[str, object] = json.loads(state_json_str)

        if index % self._keyframe_interval == 0:
            entry = InternalEntry(
                index=index,
                snapshot_type="keyframe",
                mutator_id=snapshot.mutator_id,
                timestamp=snapshot.timestamp,
                full_state_json=state_json_str,
                delta=None,
            )
        else:
            # Compute delta from previous version
            prev_json_dict = self._reconstruct_json(state_id, index - 1)
            delta = compute_delta(prev_json_dict, state_json_dict)
            entry = InternalEntry(
                index=index,
                snapshot_type="delta",
                mutator_id=snapshot.mutator_id,
                timestamp=snapshot.timestamp,
                full_state_json=None,
                delta=delta,
            )

        history.append(entry)

    async def get_latest(self, state_id: str) -> Optional[Snapshot[TState]]:
        """Return the most recent snapshot, fully reconstructed."""
        history = self._storage.get(state_id)
        if not history:
            return None
        return self._reconstruct_snapshot(state_id, len(history) - 1)

    async def checkout(self, state_id: str, version: int) -> Optional[Snapshot[TState]]:
        """Revert to *version*, deleting all entries above it."""
        history = self._storage.get(state_id)
        if not history:
            return None
        if version < 0 or version >= len(history):
            return None

        snapshot = self._reconstruct_snapshot(state_id, version)

        # Truncate history
        self._storage[state_id] = history[: version + 1]

        # Ensure the entry at *version* is a keyframe so future
        # deltas have a valid base after truncation.
        entry = self._storage[state_id][version]
        if entry.snapshot_type == "delta":
            full_json_str = json.dumps(
                self._reconstruct_json(state_id, version),
                sort_keys=True,
                default=str,
            )
            entry.snapshot_type = "keyframe"
            entry.full_state_json = full_json_str
            entry.delta = None

        return snapshot

    async def list_history(
        self, state_id: str, history_filter: HistoryFilter
    ) -> List[Snapshot[TState]]:
        """Return fully-reconstructed snapshots matching *history_filter*."""
        history = self._storage.get(state_id)
        if not history:
            return []

        results: List[Snapshot[TState]] = []
        for entry in history:
            if (
                history_filter.from_version is not None
                and entry.index < history_filter.from_version
            ):
                continue
            if (
                history_filter.to_version is not None
                and entry.index > history_filter.to_version
            ):
                continue
            if (
                history_filter.from_time is not None
                and entry.timestamp < history_filter.from_time
            ):
                continue
            if (
                history_filter.to_time is not None
                and entry.timestamp > history_filter.to_time
            ):
                continue
            results.append(self._reconstruct_snapshot(state_id, entry.index))
        return results

    async def save(self, state_id: str, state: TState) -> None:
        """Save state by appending a new snapshot."""
        from datetime import datetime, timezone

        latest = await self.get_latest(state_id)
        index = (latest.index + 1) if latest is not None else 0

        snapshot: Snapshot[TState] = Snapshot(
            mutator_id="__save__",
            timestamp=datetime.now(timezone.utc),
            state=state,
            index=index,
        )
        await self.append(state_id, snapshot)

    async def get(self, state_id: str) -> Optional[TState]:
        """Get the current state by returning the latest snapshot's state."""
        latest = await self.get_latest(state_id)
        if latest is None:
            return None
        return latest.state

    async def delete(self, state_id: str) -> bool:
        """Delete all history for *state_id*."""
        if state_id in self._storage:
            del self._storage[state_id]
            return True
        return False

    async def exists(self, state_id: str) -> bool:
        """Check whether any history exists for *state_id*."""
        history = self._storage.get(state_id)
        return history is not None and len(history) > 0

    def _reconstruct_json(self, state_id: str, index: int) -> Dict[str, object]:
        """Reconstruct the full JSON dict at *index* by walking the delta chain."""
        history = self._storage[state_id]
        entry = history[index]

        if entry.snapshot_type == "keyframe":
            assert entry.full_state_json is not None
            result: Dict[str, object] = json.loads(entry.full_state_json)
            return result

        # Find nearest preceding keyframe
        kf_index = index
        while kf_index >= 0 and history[kf_index].snapshot_type != "keyframe":
            kf_index -= 1

        assert kf_index >= 0, "No keyframe found before delta"
        kf_entry = history[kf_index]
        assert kf_entry.full_state_json is not None
        current: Dict[str, object] = json.loads(kf_entry.full_state_json)

        for i in range(kf_index + 1, index + 1):
            delta_entry = history[i]
            assert delta_entry.delta is not None
            current = apply_delta(current, delta_entry.delta)

        return current

    def _reconstruct_snapshot(self, state_id: str, index: int) -> Snapshot[TState]:
        """Build a full Snapshot at *index*."""
        history = self._storage[state_id]
        entry = history[index]
        full_json = self._reconstruct_json(state_id, index)
        full_json_str = json.dumps(full_json, sort_keys=True, default=str)

        state = self._state_class.from_json(full_json_str)
        # The cast is safe because _state_class: Type[TState] and
        # from_json returns an instance of cls.
        typed_state = cast(TState, state)

        return Snapshot(
            mutator_id=entry.mutator_id,
            timestamp=entry.timestamp,
            state=typed_state,
            index=entry.index,
            snapshot_type=entry.snapshot_type,
        )
