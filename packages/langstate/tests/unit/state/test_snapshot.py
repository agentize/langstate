"""Tests for snapshot store implementations."""

import pytest

from core.state.canonical.state import CanonicalState
from core.state.interpretive.schema import InterpretiveFieldState, ValueConfidence
from core.state.interpretive.state import InterpretiveState
from core.state.snapshot import InMemorySnapshotStore, Snapshot


class TestInMemorySnapshotStoreWithCanonicalState:
    """Tests for InMemorySnapshotStore with CanonicalState."""

    @pytest.fixture
    def store(self) -> InMemorySnapshotStore[CanonicalState]:
        return InMemorySnapshotStore[CanonicalState]()

    @pytest.fixture
    def sample_state(self) -> CanonicalState:
        state = CanonicalState()
        state.set_field("name", "John")
        state.set_field("age", 30)
        return state

    @pytest.mark.asyncio
    async def test_record_snapshot_stores_copy(
        self, store: InMemorySnapshotStore[CanonicalState], sample_state: CanonicalState
    ) -> None:
        """Snapshot should store a deep copy, not the original."""
        await store.record_snapshot("mutator_1", sample_state)

        # Modify original state
        sample_state.set_field("name", "Jane")

        # Snapshot should still have original value
        snapshots = await store.get_snapshots()
        assert len(snapshots) == 1
        assert snapshots[0].state.get_field("name") == "John"

    @pytest.mark.asyncio
    async def test_record_multiple_snapshots(
        self, store: InMemorySnapshotStore[CanonicalState], sample_state: CanonicalState
    ) -> None:
        """Should record multiple snapshots in order."""
        await store.record_snapshot("mutator_1", sample_state)

        sample_state.set_field("name", "Jane")
        await store.record_snapshot("mutator_2", sample_state)

        snapshots = await store.get_snapshots()
        assert len(snapshots) == 2
        assert snapshots[0].state.get_field("name") == "John"
        assert snapshots[1].state.get_field("name") == "Jane"
        assert snapshots[0].index == 0
        assert snapshots[1].index == 1

    @pytest.mark.asyncio
    async def test_get_snapshots_by_mutator(
        self, store: InMemorySnapshotStore[CanonicalState], sample_state: CanonicalState
    ) -> None:
        """Should filter snapshots by mutator ID."""
        await store.record_snapshot("mutator_1", sample_state)
        sample_state.set_field("name", "Jane")
        await store.record_snapshot("mutator_2", sample_state)
        sample_state.set_field("name", "Bob")
        await store.record_snapshot("mutator_1", sample_state)

        mutator_1_snapshots = await store.get_snapshots_by_mutator("mutator_1")
        assert len(mutator_1_snapshots) == 2
        assert mutator_1_snapshots[0].state.get_field("name") == "John"
        assert mutator_1_snapshots[1].state.get_field("name") == "Bob"

    @pytest.mark.asyncio
    async def test_get_latest_returns_most_recent(
        self, store: InMemorySnapshotStore[CanonicalState], sample_state: CanonicalState
    ) -> None:
        """Should return the most recent snapshot."""
        await store.record_snapshot("mutator_1", sample_state)
        sample_state.set_field("name", "Jane")
        await store.record_snapshot("mutator_2", sample_state)

        latest = await store.get_latest()
        assert latest is not None
        assert latest.state.get_field("name") == "Jane"
        assert latest.mutator_id == "mutator_2"

    @pytest.mark.asyncio
    async def test_get_latest_returns_none_when_empty(
        self, store: InMemorySnapshotStore[CanonicalState]
    ) -> None:
        """Should return None when no snapshots exist."""
        latest = await store.get_latest()
        assert latest is None

    @pytest.mark.asyncio
    async def test_clear_removes_all_snapshots(
        self, store: InMemorySnapshotStore[CanonicalState], sample_state: CanonicalState
    ) -> None:
        """Clear should remove all snapshots."""
        await store.record_snapshot("mutator_1", sample_state)
        await store.record_snapshot("mutator_2", sample_state)

        await store.clear()

        assert await store.count() == 0
        assert await store.get_latest() is None

    @pytest.mark.asyncio
    async def test_count_returns_correct_number(
        self, store: InMemorySnapshotStore[CanonicalState], sample_state: CanonicalState
    ) -> None:
        """Count should return the number of stored snapshots."""
        assert await store.count() == 0

        await store.record_snapshot("mutator_1", sample_state)
        assert await store.count() == 1

        await store.record_snapshot("mutator_2", sample_state)
        assert await store.count() == 2

    @pytest.mark.asyncio
    async def test_snapshot_has_timestamp(
        self, store: InMemorySnapshotStore[CanonicalState], sample_state: CanonicalState
    ) -> None:
        """Snapshots should have timestamps."""
        await store.record_snapshot("mutator_1", sample_state)

        snapshots = await store.get_snapshots()
        assert snapshots[0].timestamp is not None


class TestInMemorySnapshotStoreWithInterpretiveState:
    """Tests for InMemorySnapshotStore with InterpretiveState."""

    @pytest.fixture
    def store(self) -> InMemorySnapshotStore[InterpretiveState]:
        return InMemorySnapshotStore[InterpretiveState]()

    @pytest.fixture
    def sample_state(self) -> InterpretiveState:
        state = InterpretiveState()
        state.set_field(
            "name",
            InterpretiveFieldState(
                inference=None, values=[ValueConfidence(value="John", confidence=0.9)]
            ),
        )
        return state

    @pytest.mark.asyncio
    async def test_record_snapshot_with_interpretive_state(
        self,
        store: InMemorySnapshotStore[InterpretiveState],
        sample_state: InterpretiveState,
    ) -> None:
        """Should correctly deep copy InterpretiveState."""
        await store.record_snapshot("mutator_1", sample_state)

        # Modify original
        field_data = sample_state.get_field("name")
        assert field_data is not None
        sample_state.set_field(
            "name",
            InterpretiveFieldState(
                inference=None, values=[ValueConfidence(value="Jane", confidence=0.8)]
            ),
        )

        # Snapshot should be unchanged
        snapshots = await store.get_snapshots()
        snapshot_field = snapshots[0].state.get_field("name")
        assert snapshot_field is not None
        assert len(snapshot_field.values) == 1
        assert snapshot_field.values[0].value == "John"
        assert snapshot_field.values[0].confidence == 0.9


class TestInMemorySnapshotStoreBoundedCapacity:
    """Tests for bounded capacity behavior."""

    @pytest.mark.asyncio
    async def test_respects_max_snapshots_limit(self) -> None:
        """Should discard oldest snapshots when limit exceeded."""
        store: InMemorySnapshotStore[CanonicalState] = InMemorySnapshotStore(
            max_snapshots=3
        )
        state = CanonicalState()

        for i in range(5):
            state.set_field("value", i)
            await store.record_snapshot(f"mutator_{i}", state)

        # Should only have last 3 snapshots
        assert await store.count() == 3
        snapshots = await store.get_snapshots()
        # Values should be 2, 3, 4 (oldest 0, 1 were discarded)
        assert snapshots[0].state.get_field("value") == 2
        assert snapshots[1].state.get_field("value") == 3
        assert snapshots[2].state.get_field("value") == 4

    @pytest.mark.asyncio
    async def test_index_continues_after_eviction(self) -> None:
        """Snapshot index should continue incrementing after eviction."""
        store: InMemorySnapshotStore[CanonicalState] = InMemorySnapshotStore(
            max_snapshots=2
        )
        state = CanonicalState()

        for i in range(5):
            state.set_field("value", i)
            await store.record_snapshot(f"mutator_{i}", state)

        snapshots = await store.get_snapshots()
        # Indices should be 3 and 4 (first 3 were evicted but indices continued)
        assert snapshots[0].index == 3
        assert snapshots[1].index == 4

    @pytest.mark.asyncio
    async def test_default_max_snapshots(self) -> None:
        """Default max_snapshots should be 100."""
        store: InMemorySnapshotStore[CanonicalState] = InMemorySnapshotStore()
        assert store.max_snapshots == 100

    @pytest.mark.asyncio
    async def test_custom_max_snapshots(self) -> None:
        """Should accept custom max_snapshots."""
        store: InMemorySnapshotStore[CanonicalState] = InMemorySnapshotStore(
            max_snapshots=50
        )
        assert store.max_snapshots == 50


class TestSnapshotDataclass:
    """Tests for the Snapshot dataclass."""

    def test_snapshot_is_immutable(self) -> None:
        """Snapshot should be immutable (frozen dataclass)."""
        from datetime import datetime, timezone

        state = CanonicalState()
        snapshot: Snapshot[CanonicalState] = Snapshot(
            mutator_id="test",
            timestamp=datetime.now(timezone.utc),
            state=state,
            index=0,
        )

        with pytest.raises(AttributeError):
            snapshot.mutator_id = "modified"  # type: ignore[misc]
