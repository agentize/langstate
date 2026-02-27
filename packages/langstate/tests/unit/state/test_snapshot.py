"""Tests for the Snapshot data model."""

from datetime import datetime, timezone

import pytest

from core.state.state.schema import ValueConfidence
from core.state.state.state import State
from core.state.snapshot import Snapshot


class TestSnapshotDataclass:
    """Tests for the Snapshot frozen dataclass."""

    def test_snapshot_is_immutable(self) -> None:
        """Snapshot should be immutable (frozen dataclass)."""
        state = State()
        snapshot: Snapshot[State] = Snapshot(
            mutator_id="test",
            timestamp=datetime.now(timezone.utc),
            state=state,
            index=0,
        )

        with pytest.raises(AttributeError):
            snapshot.mutator_id = "modified"  # type: ignore[misc]

    def test_snapshot_default_type_is_keyframe(self) -> None:
        """Default snapshot_type should be 'keyframe'."""
        state = State()
        snapshot: Snapshot[State] = Snapshot(
            mutator_id="test",
            timestamp=datetime.now(timezone.utc),
            state=state,
            index=0,
        )
        assert snapshot.snapshot_type == "keyframe"

    def test_snapshot_type_delta(self) -> None:
        """snapshot_type can be set to 'delta'."""
        state = State()
        snapshot: Snapshot[State] = Snapshot(
            mutator_id="test",
            timestamp=datetime.now(timezone.utc),
            state=state,
            index=1,
            snapshot_type="delta",
        )
        assert snapshot.snapshot_type == "delta"

    def test_snapshot_stores_state(self) -> None:
        """Snapshot should store the provided state."""
        state = State()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        snapshot: Snapshot[State] = Snapshot(
            mutator_id="mut_1",
            timestamp=datetime.now(timezone.utc),
            state=state,
            index=0,
        )

        field = snapshot.state.get_field("name")
        assert field is not None
        assert field.values[0].value == "John"

    def test_snapshot_preserves_mutator_id(self) -> None:
        """Should preserve the mutator_id."""
        state = State()
        snapshot: Snapshot[State] = Snapshot(
            mutator_id="my_mutator",
            timestamp=datetime.now(timezone.utc),
            state=state,
            index=5,
        )
        assert snapshot.mutator_id == "my_mutator"

    def test_snapshot_preserves_index(self) -> None:
        """Should preserve the index."""
        state = State()
        snapshot: Snapshot[State] = Snapshot(
            mutator_id="test",
            timestamp=datetime.now(timezone.utc),
            state=state,
            index=42,
        )
        assert snapshot.index == 42

    def test_snapshot_preserves_timestamp(self) -> None:
        """Should preserve the timestamp."""
        ts = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        state = State()
        snapshot: Snapshot[State] = Snapshot(
            mutator_id="test",
            timestamp=ts,
            state=state,
            index=0,
        )
        assert snapshot.timestamp == ts
