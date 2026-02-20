"""Tests for snapshot store implementations."""

import pytest

from core.state.state.schema import InterpretiveField, ValueConfidence
from core.state.state.state import State
from core.state.snapshot import InMemorySnapshotStore, Snapshot


class TestInMemorySnapshotStoreWithState:
    """Tests for InMemorySnapshotStore with State."""

    @pytest.fixture
    def store(self) -> InMemorySnapshotStore[State]:
        return InMemorySnapshotStore[State]()

    @pytest.fixture
    def sample_state(self) -> State:
        state = State()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))
        state.add_value("age", ValueConfidence(value=30, confidence=0.85))
        return state

    @pytest.mark.asyncio
    async def test_record_snapshot_stores_copy(
        self, store: InMemorySnapshotStore[State], sample_state: State
    ) -> None:
        """Snapshot should store a deep copy, not the original."""
        await store.record_snapshot("mutator_1", sample_state)

        # Modify original state
        sample_state.add_value("name", ValueConfidence(value="Jane", confidence=0.95))

        # Snapshot should still have original value
        snapshots = await store.get_snapshots()
        assert len(snapshots) == 1
        field = snapshots[0].state.get_field("name")
        assert field is not None
        assert field.values[0].value == "John"

    @pytest.mark.asyncio
    async def test_record_multiple_snapshots(
        self, store: InMemorySnapshotStore[State], sample_state: State
    ) -> None:
        """Should record multiple snapshots in order."""
        await store.record_snapshot("mutator_1", sample_state)

        state2 = State()
        state2.add_value("name", ValueConfidence(value="Jane", confidence=0.9))
        await store.record_snapshot("mutator_2", state2)

        snapshots = await store.get_snapshots()
        assert len(snapshots) == 2
        field0 = snapshots[0].state.get_field("name")
        field1 = snapshots[1].state.get_field("name")
        assert field0 is not None
        assert field0.values[0].value == "John"
        assert field1 is not None
        assert field1.values[0].value == "Jane"
        assert snapshots[0].index == 0
        assert snapshots[1].index == 1

    @pytest.mark.asyncio
    async def test_get_snapshots_by_mutator(
        self, store: InMemorySnapshotStore[State], sample_state: State
    ) -> None:
        """Should filter snapshots by mutator ID."""
        await store.record_snapshot("mutator_1", sample_state)

        state2 = State()
        state2.add_value("name", ValueConfidence(value="Jane", confidence=0.9))
        await store.record_snapshot("mutator_2", state2)

        state3 = State()
        state3.add_value("name", ValueConfidence(value="Bob", confidence=0.9))
        await store.record_snapshot("mutator_1", state3)

        mutator_1_snapshots = await store.get_snapshots_by_mutator("mutator_1")
        assert len(mutator_1_snapshots) == 2
        field0 = mutator_1_snapshots[0].state.get_field("name")
        field1 = mutator_1_snapshots[1].state.get_field("name")
        assert field0 is not None
        assert field0.values[0].value == "John"
        assert field1 is not None
        assert field1.values[0].value == "Bob"

    @pytest.mark.asyncio
    async def test_get_latest_returns_most_recent(
        self, store: InMemorySnapshotStore[State], sample_state: State
    ) -> None:
        """Should return the most recent snapshot."""
        await store.record_snapshot("mutator_1", sample_state)

        state2 = State()
        state2.add_value("name", ValueConfidence(value="Jane", confidence=0.9))
        await store.record_snapshot("mutator_2", state2)

        latest = await store.get_latest()
        assert latest is not None
        field = latest.state.get_field("name")
        assert field is not None
        assert field.values[0].value == "Jane"
        assert latest.mutator_id == "mutator_2"

    @pytest.mark.asyncio
    async def test_get_latest_returns_none_when_empty(
        self, store: InMemorySnapshotStore[State]
    ) -> None:
        """Should return None when no snapshots exist."""
        latest = await store.get_latest()
        assert latest is None

    @pytest.mark.asyncio
    async def test_clear_removes_all_snapshots(
        self, store: InMemorySnapshotStore[State], sample_state: State
    ) -> None:
        """Clear should remove all snapshots."""
        await store.record_snapshot("mutator_1", sample_state)
        await store.record_snapshot("mutator_2", sample_state)

        await store.clear()

        assert await store.count() == 0
        assert await store.get_latest() is None

    @pytest.mark.asyncio
    async def test_count_returns_correct_number(
        self, store: InMemorySnapshotStore[State], sample_state: State
    ) -> None:
        """Count should return the number of stored snapshots."""
        assert await store.count() == 0

        await store.record_snapshot("mutator_1", sample_state)
        assert await store.count() == 1

        await store.record_snapshot("mutator_2", sample_state)
        assert await store.count() == 2

    @pytest.mark.asyncio
    async def test_snapshot_has_timestamp(
        self, store: InMemorySnapshotStore[State], sample_state: State
    ) -> None:
        """Snapshots should have timestamps."""
        await store.record_snapshot("mutator_1", sample_state)

        snapshots = await store.get_snapshots()
        assert snapshots[0].timestamp is not None


class TestInMemorySnapshotStoreDeepCopy:
    """Tests for deep copy behavior with State."""

    @pytest.fixture
    def store(self) -> InMemorySnapshotStore[State]:
        return InMemorySnapshotStore[State]()

    @pytest.fixture
    def sample_state(self) -> State:
        state = State()
        state.set_field(
            "name",
            InterpretiveField(
                inference=None, values=[ValueConfidence(value="John", confidence=0.9)]
            ),
        )
        return state

    @pytest.mark.asyncio
    async def test_record_snapshot_with_state(
        self,
        store: InMemorySnapshotStore[State],
        sample_state: State,
    ) -> None:
        """Should correctly deep copy State."""
        await store.record_snapshot("mutator_1", sample_state)

        # Modify original
        sample_state.set_field(
            "name",
            InterpretiveField(
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
        store: InMemorySnapshotStore[State] = InMemorySnapshotStore(max_snapshots=3)

        for i in range(5):
            state = State()
            state.add_value("value", ValueConfidence(value=i, confidence=0.9))
            await store.record_snapshot(f"mutator_{i}", state)

        # Should only have last 3 snapshots
        assert await store.count() == 3
        snapshots = await store.get_snapshots()
        # Values should be 2, 3, 4 (oldest 0, 1 were discarded)
        for idx, expected_val in enumerate([2, 3, 4]):
            field = snapshots[idx].state.get_field("value")
            assert field is not None
            assert field.values[0].value == expected_val

    @pytest.mark.asyncio
    async def test_index_continues_after_eviction(self) -> None:
        """Snapshot index should continue incrementing after eviction."""
        store: InMemorySnapshotStore[State] = InMemorySnapshotStore(max_snapshots=2)

        for i in range(5):
            state = State()
            state.add_value("value", ValueConfidence(value=i, confidence=0.9))
            await store.record_snapshot(f"mutator_{i}", state)

        snapshots = await store.get_snapshots()
        # Indices should be 3 and 4 (first 3 were evicted but indices continued)
        assert snapshots[0].index == 3
        assert snapshots[1].index == 4

    @pytest.mark.asyncio
    async def test_default_max_snapshots(self) -> None:
        """Default max_snapshots should be 100."""
        store: InMemorySnapshotStore[State] = InMemorySnapshotStore()
        assert store.max_snapshots == 100

    @pytest.mark.asyncio
    async def test_custom_max_snapshots(self) -> None:
        """Should accept custom max_snapshots."""
        store: InMemorySnapshotStore[State] = InMemorySnapshotStore(max_snapshots=50)
        assert store.max_snapshots == 50


class TestSnapshotDataclass:
    """Tests for the Snapshot dataclass."""

    def test_snapshot_is_immutable(self) -> None:
        """Snapshot should be immutable (frozen dataclass)."""
        from datetime import datetime, timezone

        state = State()
        snapshot: Snapshot[State] = Snapshot(
            mutator_id="test",
            timestamp=datetime.now(timezone.utc),
            state=state,
            index=0,
        )

        with pytest.raises(AttributeError):
            snapshot.mutator_id = "modified"  # type: ignore[misc]
