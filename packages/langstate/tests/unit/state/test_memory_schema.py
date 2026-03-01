"""Unit tests for internal repository schemas.

Covers InternalEntry and HistoryFilter Pydantic models.
"""

from datetime import datetime

from core.state.repository.snapshot_repository.memory.schema import InternalEntry
from core.state.repository.snapshot_repository.base.schema import HistoryFilter


# ════════════════════════════════════════════════════════════════════
# InternalEntry model
# ════════════════════════════════════════════════════════════════════


class TestInternalEntry:
    """Tests for InternalEntry Pydantic model."""

    def test_keyframe_entry(self) -> None:
        now = datetime.now()
        entry = InternalEntry(
            index=0,
            snapshot_type="keyframe",
            mutator_id="m1",
            timestamp=now,
            full_state_json='{"nodes": []}',
        )
        assert entry.index == 0
        assert entry.snapshot_type == "keyframe"
        assert entry.mutator_id == "m1"
        assert entry.timestamp == now
        assert entry.full_state_json is not None
        assert entry.delta is None

    def test_delta_entry(self) -> None:
        now = datetime.now()
        entry = InternalEntry(
            index=1,
            snapshot_type="delta",
            mutator_id="m2",
            timestamp=now,
            delta={"added": {"x": 1}},
        )
        assert entry.index == 1
        assert entry.snapshot_type == "delta"
        assert entry.full_state_json is None
        assert entry.delta == {"added": {"x": 1}}

    def test_defaults(self) -> None:
        entry = InternalEntry(
            index=0,
            snapshot_type="keyframe",
            mutator_id="m",
            timestamp=datetime.now(),
        )
        assert entry.full_state_json is None
        assert entry.delta is None


# ════════════════════════════════════════════════════════════════════
# HistoryFilter model
# ════════════════════════════════════════════════════════════════════


class TestHistoryFilter:
    """Tests for HistoryFilter Pydantic model."""

    def test_all_defaults_none(self) -> None:
        f = HistoryFilter()
        assert f.from_version is None
        assert f.to_version is None
        assert f.from_time is None
        assert f.to_time is None

    def test_version_bounds(self) -> None:
        f = HistoryFilter(from_version=0, to_version=5)
        assert f.from_version == 0
        assert f.to_version == 5

    def test_time_bounds(self) -> None:
        t1 = datetime(2025, 1, 1)
        t2 = datetime(2025, 12, 31)
        f = HistoryFilter(from_time=t1, to_time=t2)
        assert f.from_time == t1
        assert f.to_time == t2

    def test_all_fields_set(self) -> None:
        t1 = datetime(2025, 1, 1)
        t2 = datetime(2025, 12, 31)
        f = HistoryFilter(from_version=1, to_version=10, from_time=t1, to_time=t2)
        assert f.from_version == 1
        assert f.to_version == 10
        assert f.from_time == t1
        assert f.to_time == t2
