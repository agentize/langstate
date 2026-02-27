"""Tests for InMemorySnapshotRepository.

Covers append, get_latest, checkout, list_history, save/get bridge,
delete, exists, get_or_create, delta/keyframe logic, and reconstruction.
"""

from datetime import datetime, timedelta, timezone

import pytest

# pyright: reportPrivateUsage=false

from core.state.snapshot.snapshot import Snapshot
from core.state.state.schema import ValueConfidence
from core.state.state.state import State
from core.state.repository.snapshot_repository import (
    InMemorySnapshotRepository,
    HistoryFilter,
)

from core.state.repository.snapshot_repository.memory.memory import (
    compute_delta,
    apply_delta,
)


def _make_state(**fields: object) -> State:
    """Helper: create a State with the given field values."""
    state = State()
    for path, value in fields.items():
        state.add_value(path, ValueConfidence(value=value, confidence=0.9))
    return state


def _make_snapshot(
    state: State,
    mutator_id: str = "mut",
    index: int = 0,
    timestamp: datetime | None = None,
) -> Snapshot[State]:
    return Snapshot(
        mutator_id=mutator_id,
        timestamp=timestamp or datetime.now(timezone.utc),
        state=state,
        index=index,
    )


# ── Keyframe / Delta logic ────────────────────────────────────────


class TestKeyframeDeltaPolicy:
    """Verify that keyframes appear at the correct intervals."""

    @pytest.fixture
    def repo(self) -> InMemorySnapshotRepository[State]:
        return InMemorySnapshotRepository(state_class=State, keyframe_interval=3)

    @pytest.mark.asyncio
    async def test_first_entry_is_keyframe(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        """Index 0 must always be a keyframe."""
        await repo.append("s", _make_snapshot(_make_state(a="v0")))
        snap = await repo.get_latest("s")
        assert snap is not None
        assert snap.snapshot_type == "keyframe"

    @pytest.mark.asyncio
    async def test_interval_creates_keyframes(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        """Every keyframe_interval-th entry should be a keyframe."""
        # interval=3 → keyframes at 0, 3, 6
        for i in range(7):
            await repo.append("s", _make_snapshot(_make_state(x=str(i))))

        history = await repo.list_history("s", HistoryFilter())
        types = [s.snapshot_type for s in history]
        assert types == [
            "keyframe",  # 0
            "delta",  # 1
            "delta",  # 2
            "keyframe",  # 3
            "delta",  # 4
            "delta",  # 5
            "keyframe",  # 6
        ]

    @pytest.mark.asyncio
    async def test_default_keyframe_interval(self) -> None:
        repo: InMemorySnapshotRepository[State] = InMemorySnapshotRepository(
            state_class=State
        )
        assert repo.keyframe_interval == 10


# ── Append & get_latest ────────────────────────────────────────────


class TestAppendAndGetLatest:
    @pytest.fixture
    def repo(self) -> InMemorySnapshotRepository[State]:
        return InMemorySnapshotRepository(state_class=State, keyframe_interval=5)

    @pytest.mark.asyncio
    async def test_get_latest_empty(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        assert await repo.get_latest("s") is None

    @pytest.mark.asyncio
    async def test_append_one_snapshot(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        state = _make_state(name="Alice")
        await repo.append("s", _make_snapshot(state, mutator_id="m1"))

        latest = await repo.get_latest("s")
        assert latest is not None
        assert latest.mutator_id == "m1"
        assert latest.index == 0
        field = latest.state.get_field("name")
        assert field is not None
        assert field.values[0].value == "Alice"

    @pytest.mark.asyncio
    async def test_append_many_snapshots(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        """Latest should always be the last appended snapshot."""
        for i in range(12):
            await repo.append(
                "s", _make_snapshot(_make_state(v=str(i)), mutator_id=f"m{i}")
            )

        latest = await repo.get_latest("s")
        assert latest is not None
        assert latest.index == 11
        field = latest.state.get_field("v")
        assert field is not None
        assert field.values[0].value == "11"

    @pytest.mark.asyncio
    async def test_independent_state_ids(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        """Different state_ids should have independent histories."""
        await repo.append("a", _make_snapshot(_make_state(x="a_val")))
        await repo.append("b", _make_snapshot(_make_state(x="b_val")))

        latest_a = await repo.get_latest("a")
        latest_b = await repo.get_latest("b")
        assert latest_a is not None
        assert latest_b is not None
        field_a = latest_a.state.get_field("x")
        assert field_a is not None
        assert field_a.values[0].value == "a_val"
        field_b = latest_b.state.get_field("x")
        assert field_b is not None
        assert field_b.values[0].value == "b_val"


# ── Checkout ───────────────────────────────────────────────────────


class TestCheckout:
    @pytest.fixture
    def repo(self) -> InMemorySnapshotRepository[State]:
        return InMemorySnapshotRepository(state_class=State, keyframe_interval=5)

    @pytest.mark.asyncio
    async def test_checkout_to_version(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        for i in range(8):
            await repo.append("s", _make_snapshot(_make_state(v=str(i))))

        result = await repo.checkout("s", 3)
        assert result is not None
        assert result.index == 3
        field = result.state.get_field("v")
        assert field is not None
        assert field.values[0].value == "3"

        # Everything above version 3 should be gone
        latest = await repo.get_latest("s")
        assert latest is not None
        assert latest.index == 3

    @pytest.mark.asyncio
    async def test_checkout_nonexistent_version(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        await repo.append("s", _make_snapshot(_make_state(v="0")))
        result = await repo.checkout("s", 99)
        assert result is None

    @pytest.mark.asyncio
    async def test_checkout_negative_version(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        await repo.append("s", _make_snapshot(_make_state(v="0")))
        result = await repo.checkout("s", -1)
        assert result is None

    @pytest.mark.asyncio
    async def test_checkout_empty_history(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        result = await repo.checkout("s", 0)
        assert result is None

    @pytest.mark.asyncio
    async def test_checkout_converts_delta_to_keyframe(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        """After checkout on a delta, that entry should become a keyframe
        so new appends can be based on it."""
        for i in range(4):
            await repo.append("s", _make_snapshot(_make_state(v=str(i))))

        # Version 2 would be a delta (interval=5, keyframe at 0)
        await repo.checkout("s", 2)

        # Append a new version (index 3 in the now-truncated history)
        await repo.append("s", _make_snapshot(_make_state(v="new")))
        latest = await repo.get_latest("s")
        assert latest is not None
        field = latest.state.get_field("v")
        assert field is not None
        assert field.values[0].value == "new"


# ── list_history ───────────────────────────────────────────────────


class TestListHistory:
    @pytest.fixture
    def repo(self) -> InMemorySnapshotRepository[State]:
        return InMemorySnapshotRepository(state_class=State, keyframe_interval=5)

    @pytest.mark.asyncio
    async def test_list_all(self, repo: InMemorySnapshotRepository[State]) -> None:
        for i in range(5):
            await repo.append("s", _make_snapshot(_make_state(v=str(i))))

        history = await repo.list_history("s", HistoryFilter())
        assert len(history) == 5
        for idx, snap in enumerate(history):
            assert snap.index == idx

    @pytest.mark.asyncio
    async def test_filter_by_version_range(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        for i in range(10):
            await repo.append("s", _make_snapshot(_make_state(v=str(i))))

        history = await repo.list_history(
            "s", HistoryFilter(from_version=3, to_version=6)
        )
        assert [s.index for s in history] == [3, 4, 5, 6]

    @pytest.mark.asyncio
    async def test_filter_by_time_range(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        base = datetime(2025, 1, 1, tzinfo=timezone.utc)
        for i in range(5):
            ts = base + timedelta(hours=i)
            await repo.append(
                "s",
                _make_snapshot(_make_state(v=str(i)), timestamp=ts),
            )

        history = await repo.list_history(
            "s",
            HistoryFilter(
                from_time=base + timedelta(hours=1),
                to_time=base + timedelta(hours=3),
            ),
        )
        assert len(history) == 3
        assert [s.index for s in history] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_combined_filter(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        base = datetime(2025, 1, 1, tzinfo=timezone.utc)
        for i in range(10):
            ts = base + timedelta(hours=i)
            await repo.append(
                "s",
                _make_snapshot(_make_state(v=str(i)), timestamp=ts),
            )

        history = await repo.list_history(
            "s",
            HistoryFilter(
                from_version=2,
                to_version=7,
                from_time=base + timedelta(hours=3),
                to_time=base + timedelta(hours=6),
            ),
        )
        assert [s.index for s in history] == [3, 4, 5, 6]

    @pytest.mark.asyncio
    async def test_list_empty_history(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        history = await repo.list_history("s", HistoryFilter())
        assert history == []

    @pytest.mark.asyncio
    async def test_filter_returns_empty_when_no_match(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        await repo.append("s", _make_snapshot(_make_state(v="0")))
        history = await repo.list_history(
            "s", HistoryFilter(from_version=100, to_version=200)
        )
        assert history == []


# ── save / get (BaseRepository bridge) ─────────────────────────────


class TestBaseRepositoryBridge:
    @pytest.fixture
    def repo(self) -> InMemorySnapshotRepository[State]:
        return InMemorySnapshotRepository(state_class=State, keyframe_interval=5)

    @pytest.mark.asyncio
    async def test_save_and_get(self, repo: InMemorySnapshotRepository[State]) -> None:
        state = _make_state(name="John")
        await repo.save("s", state)

        result = await repo.get("s")
        assert result is not None
        field = result.get_field("name")
        assert field is not None
        assert field.values[0].value == "John"

    @pytest.mark.asyncio
    async def test_save_increments_version(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        await repo.save("s", _make_state(v="0"))
        await repo.save("s", _make_state(v="1"))
        await repo.save("s", _make_state(v="2"))

        latest = await repo.get_latest("s")
        assert latest is not None
        assert latest.index == 2

    @pytest.mark.asyncio
    async def test_get_returns_none_when_empty(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        assert await repo.get("nonexistent") is None


# ── delete / exists ────────────────────────────────────────────────


class TestDeleteAndExists:
    @pytest.fixture
    def repo(self) -> InMemorySnapshotRepository[State]:
        return InMemorySnapshotRepository(state_class=State, keyframe_interval=5)

    @pytest.mark.asyncio
    async def test_exists_true(self, repo: InMemorySnapshotRepository[State]) -> None:
        await repo.append("s", _make_snapshot(_make_state(v="0")))
        assert await repo.exists("s") is True

    @pytest.mark.asyncio
    async def test_exists_false(self, repo: InMemorySnapshotRepository[State]) -> None:
        assert await repo.exists("s") is False

    @pytest.mark.asyncio
    async def test_delete_existing(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        await repo.append("s", _make_snapshot(_make_state(v="0")))
        assert await repo.delete("s") is True
        assert await repo.exists("s") is False
        assert await repo.get_latest("s") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        assert await repo.delete("missing") is False


# ── get_or_create (inherited) ──────────────────────────────────────


class TestGetOrCreate:
    @pytest.fixture
    def repo(self) -> InMemorySnapshotRepository[State]:
        return InMemorySnapshotRepository(state_class=State, keyframe_interval=5)

    @pytest.mark.asyncio
    async def test_get_or_create_creates(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        result = await repo.get_or_create("s", lambda: _make_state(v="factory"))
        field = result.get_field("v")
        assert field is not None
        assert field.values[0].value == "factory"

    @pytest.mark.asyncio
    async def test_get_or_create_returns_existing(
        self, repo: InMemorySnapshotRepository[State]
    ) -> None:
        await repo.save("s", _make_state(v="existing"))
        result = await repo.get_or_create("s", lambda: _make_state(v="factory"))
        field = result.get_field("v")
        assert field is not None
        assert field.values[0].value == "existing"


# ── Delta reconstruction accuracy ─────────────────────────────────


class TestDeltaReconstruction:
    """Ensure state reconstructed from deltas matches the original."""

    @pytest.mark.asyncio
    async def test_reconstruction_after_many_appends(self) -> None:
        repo: InMemorySnapshotRepository[State] = InMemorySnapshotRepository(
            state_class=State, keyframe_interval=3
        )

        expected_values: list[tuple[str, str]] = []
        for i in range(15):
            state = _make_state(counter=str(i), label=f"step_{i}")
            expected_values.append((str(i), f"step_{i}"))
            await repo.append("s", _make_snapshot(state, mutator_id=f"m{i}"))

        # Verify every single snapshot reconstructs correctly
        history = await repo.list_history("s", HistoryFilter())
        assert len(history) == 15
        for idx, snap in enumerate(history):
            counter = snap.state.get_field("counter")
            label = snap.state.get_field("label")
            assert counter is not None
            assert label is not None
            assert counter.values[0].value == expected_values[idx][0]
            assert label.values[0].value == expected_values[idx][1]

    @pytest.mark.asyncio
    async def test_reconstruction_with_field_removal(self) -> None:
        """Delta should handle fields that are added/removed between versions."""
        repo: InMemorySnapshotRepository[State] = InMemorySnapshotRepository(
            state_class=State, keyframe_interval=5
        )

        # Version 0: a, b
        s0 = _make_state(a="1", b="2")
        await repo.append("s", _make_snapshot(s0))

        # Version 1: a, c  (b removed, c added)
        s1 = _make_state(a="1", c="3")
        await repo.append("s", _make_snapshot(s1))

        history = await repo.list_history("s", HistoryFilter())
        # Version 0 should have a, b
        v0_fields = history[0].state.get_all_fields()
        assert "a" in v0_fields
        assert "b" in v0_fields
        assert "c" not in v0_fields

        # Version 1 should have a, c
        v1_fields = history[1].state.get_all_fields()
        assert "a" in v1_fields
        assert "c" in v1_fields
        # b was removed — it should not be present
        assert "b" not in v1_fields

    @pytest.mark.asyncio
    async def test_reconstruction_with_value_change(self) -> None:
        """Delta should handle values that change between versions."""
        repo: InMemorySnapshotRepository[State] = InMemorySnapshotRepository(
            state_class=State, keyframe_interval=5
        )

        s0 = _make_state(name="Alice")
        await repo.append("s", _make_snapshot(s0))

        s1 = _make_state(name="Bob")
        await repo.append("s", _make_snapshot(s1))

        history = await repo.list_history("s", HistoryFilter())
        name0 = history[0].state.get_field("name")
        name1 = history[1].state.get_field("name")
        assert name0 is not None
        assert name0.values[0].value == "Alice"
        assert name1 is not None
        assert name1.values[0].value == "Bob"


# ── Custom keyframe_interval ──────────────────────────────────────


class TestCustomKeyframeInterval:
    @pytest.mark.asyncio
    async def test_interval_1_all_keyframes(self) -> None:
        repo: InMemorySnapshotRepository[State] = InMemorySnapshotRepository(
            state_class=State, keyframe_interval=1
        )
        for i in range(5):
            await repo.append("s", _make_snapshot(_make_state(v=str(i))))

        history = await repo.list_history("s", HistoryFilter())
        assert all(s.snapshot_type == "keyframe" for s in history)

    @pytest.mark.asyncio
    async def test_interval_2(self) -> None:
        repo: InMemorySnapshotRepository[State] = InMemorySnapshotRepository(
            state_class=State, keyframe_interval=2
        )
        for i in range(6):
            await repo.append("s", _make_snapshot(_make_state(v=str(i))))

        history = await repo.list_history("s", HistoryFilter())
        types = [s.snapshot_type for s in history]
        assert types == ["keyframe", "delta", "keyframe", "delta", "keyframe", "delta"]


# ── HistoryFilter edge cases ──────────────────────────────────────


class TestHistoryFilterEdgeCases:
    @pytest.mark.asyncio
    async def test_only_from_version(self) -> None:
        repo: InMemorySnapshotRepository[State] = InMemorySnapshotRepository(
            state_class=State, keyframe_interval=5
        )
        for i in range(5):
            await repo.append("s", _make_snapshot(_make_state(v=str(i))))

        history = await repo.list_history("s", HistoryFilter(from_version=3))
        assert [s.index for s in history] == [3, 4]

    @pytest.mark.asyncio
    async def test_only_to_version(self) -> None:
        repo: InMemorySnapshotRepository[State] = InMemorySnapshotRepository(
            state_class=State, keyframe_interval=5
        )
        for i in range(5):
            await repo.append("s", _make_snapshot(_make_state(v=str(i))))

        history = await repo.list_history("s", HistoryFilter(to_version=2))
        assert [s.index for s in history] == [0, 1, 2]

    @pytest.mark.asyncio
    async def test_only_from_time(self) -> None:
        repo: InMemorySnapshotRepository[State] = InMemorySnapshotRepository(
            state_class=State, keyframe_interval=5
        )
        base = datetime(2025, 6, 1, tzinfo=timezone.utc)
        for i in range(5):
            ts = base + timedelta(days=i)
            await repo.append("s", _make_snapshot(_make_state(v=str(i)), timestamp=ts))

        history = await repo.list_history(
            "s", HistoryFilter(from_time=base + timedelta(days=3))
        )
        assert [s.index for s in history] == [3, 4]

    @pytest.mark.asyncio
    async def test_only_to_time(self) -> None:
        repo: InMemorySnapshotRepository[State] = InMemorySnapshotRepository(
            state_class=State, keyframe_interval=5
        )
        base = datetime(2025, 6, 1, tzinfo=timezone.utc)
        for i in range(5):
            ts = base + timedelta(days=i)
            await repo.append("s", _make_snapshot(_make_state(v=str(i)), timestamp=ts))

        history = await repo.list_history(
            "s", HistoryFilter(to_time=base + timedelta(days=1))
        )
        assert [s.index for s in history] == [0, 1]


# ── Checkout + Append after checkout ───────────────────────────────


class TestCheckoutAndResume:
    @pytest.mark.asyncio
    async def test_append_after_checkout(self) -> None:
        """After checkout, appending should continue from the checkout version."""
        repo: InMemorySnapshotRepository[State] = InMemorySnapshotRepository(
            state_class=State, keyframe_interval=5
        )
        for i in range(8):
            await repo.append("s", _make_snapshot(_make_state(v=str(i))))

        # Checkout to version 3
        await repo.checkout("s", 3)

        # Append 2 more
        await repo.append("s", _make_snapshot(_make_state(v="new_4")))
        await repo.append("s", _make_snapshot(_make_state(v="new_5")))

        latest = await repo.get_latest("s")
        assert latest is not None
        assert latest.index == 5  # 0..3 + 2 new

        history = await repo.list_history("s", HistoryFilter())
        assert len(history) == 6

        field = history[5].state.get_field("v")
        assert field is not None
        assert field.values[0].value == "new_5"

    @pytest.mark.asyncio
    async def test_checkout_to_zero(self) -> None:
        """Checkout to version 0 should leave only one entry."""
        repo: InMemorySnapshotRepository[State] = InMemorySnapshotRepository(
            state_class=State, keyframe_interval=5
        )
        for i in range(5):
            await repo.append("s", _make_snapshot(_make_state(v=str(i))))

        result = await repo.checkout("s", 0)
        assert result is not None
        field = result.state.get_field("v")
        assert field is not None
        assert field.values[0].value == "0"

        history = await repo.list_history("s", HistoryFilter())
        assert len(history) == 1


# ── Delta / keyframe utility functions ─────────────────────────────


class TestComputeDelta:
    """Unit tests for the _compute_delta helper."""

    def test_no_changes(self) -> None:
        old = {"a": 1, "b": 2}
        delta = compute_delta(old, old)
        assert delta == {}

    def test_added_keys(self) -> None:
        delta = compute_delta({"a": 1}, {"a": 1, "b": 2})
        assert delta == {"added": {"b": 2}}

    def test_removed_keys(self) -> None:
        delta = compute_delta({"a": 1, "b": 2}, {"a": 1})
        assert "removed" in delta
        removed = delta["removed"]
        assert isinstance(removed, list)
        assert "b" in removed

    def test_modified_keys(self) -> None:
        delta = compute_delta({"a": 1}, {"a": 99})
        assert delta == {"modified": {"a": 99}}

    def test_all_changes(self) -> None:
        old: dict[str, object] = {"keep": 1, "modify": "old", "remove": True}
        new: dict[str, object] = {"keep": 1, "modify": "new", "add": "fresh"}
        delta = compute_delta(old, new)
        assert "added" in delta
        assert delta["added"] == {"add": "fresh"}
        assert "removed" in delta
        removed = delta["removed"]
        assert isinstance(removed, list)
        assert "remove" in removed
        assert "modified" in delta
        assert delta["modified"] == {"modify": "new"}


class TestApplyDelta:
    """Unit tests for the _apply_delta helper."""

    def test_empty_delta(self) -> None:
        base = {"a": 1}
        result = apply_delta(base, {})
        assert result == {"a": 1}

    def test_add_keys(self) -> None:
        result = apply_delta({"a": 1}, {"added": {"b": 2}})
        assert result == {"a": 1, "b": 2}

    def test_remove_keys(self) -> None:
        result = apply_delta({"a": 1, "b": 2}, {"removed": ["b"]})
        assert result == {"a": 1}

    def test_modify_keys(self) -> None:
        result = apply_delta({"a": 1}, {"modified": {"a": 99}})
        assert result == {"a": 99}

    def test_all_operations(self) -> None:
        base: dict[str, object] = {"keep": 1, "modify": "old", "remove": True}
        delta: dict[str, object] = {
            "added": {"new": "x"},
            "removed": ["remove"],
            "modified": {"modify": "new"},
        }
        result = apply_delta(base, delta)
        assert result == {"keep": 1, "modify": "new", "new": "x"}

    def test_remove_nonexistent_key(self) -> None:
        """Removing a key that doesn't exist should not fail."""
        result = apply_delta({"a": 1}, {"removed": ["missing"]})
        assert result == {"a": 1}
