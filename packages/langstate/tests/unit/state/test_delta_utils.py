"""Unit tests for delta utilities (compute_delta / apply_delta).

Dedicated unit tests covering all branch paths in the delta
compression utility functions.
"""

from core.state.repository.snapshot_repository.memory.utils import (
    apply_delta,
    compute_delta,
)


# ════════════════════════════════════════════════════════════════════
# compute_delta
# ════════════════════════════════════════════════════════════════════


class TestComputeDelta:
    """Tests for compute_delta function."""

    def test_identical_dicts_returns_empty(self) -> None:
        old = {"a": 1, "b": 2}
        new = {"a": 1, "b": 2}
        delta = compute_delta(old, new)
        assert delta == {}

    def test_both_empty_returns_empty(self) -> None:
        delta = compute_delta({}, {})
        assert delta == {}

    def test_added_keys_only(self) -> None:
        old: dict[str, object] = {}
        new = {"x": 10, "y": 20}
        delta = compute_delta(old, new)
        assert "added" in delta
        assert delta["added"] == {"x": 10, "y": 20}
        assert "removed" not in delta
        assert "modified" not in delta

    def test_removed_keys_only(self) -> None:
        old = {"x": 10, "y": 20}
        new: dict[str, object] = {}
        delta = compute_delta(old, new)
        assert "removed" in delta
        assert set(delta["removed"]) == {"x", "y"}  # type: ignore[arg-type]
        assert "added" not in delta
        assert "modified" not in delta

    def test_modified_keys_only(self) -> None:
        old = {"x": 1}
        new = {"x": 2}
        delta = compute_delta(old, new)
        assert "modified" in delta
        assert delta["modified"] == {"x": 2}
        assert "added" not in delta
        assert "removed" not in delta

    def test_all_three_operations(self) -> None:
        old: dict[str, object] = {
            "keep": "same",
            "change": "old_val",
            "remove_me": True,
        }
        new: dict[str, object] = {"keep": "same", "change": "new_val", "add_me": 42}
        delta = compute_delta(old, new)
        assert "added" in delta
        assert delta["added"] == {"add_me": 42}
        assert "removed" in delta
        assert "remove_me" in delta["removed"]  # type: ignore[operator]
        assert "modified" in delta
        assert delta["modified"] == {"change": "new_val"}

    def test_nested_dict_change_detected(self) -> None:
        """Changes inside nested dicts should be detected via JSON serialization."""
        old = {"nested": {"a": 1}}
        new = {"nested": {"a": 2}}
        delta = compute_delta(old, new)
        assert "modified" in delta

    def test_same_nested_dict_not_modified(self) -> None:
        old = {"nested": {"a": 1}}
        new = {"nested": {"a": 1}}
        delta = compute_delta(old, new)
        assert delta == {}


# ════════════════════════════════════════════════════════════════════
# apply_delta
# ════════════════════════════════════════════════════════════════════


class TestApplyDelta:
    """Tests for apply_delta function."""

    def test_empty_delta_returns_copy(self) -> None:
        base = {"a": 1, "b": 2}
        result = apply_delta(base, {})
        assert result == base

    def test_add_keys(self) -> None:
        base = {"a": 1}
        delta = {"added": {"b": 2, "c": 3}}
        result = apply_delta(base, delta)
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_remove_keys(self) -> None:
        base = {"a": 1, "b": 2, "c": 3}
        delta = {"removed": ["b", "c"]}
        result = apply_delta(base, delta)
        assert result == {"a": 1}

    def test_modify_keys(self) -> None:
        base = {"a": 1, "b": 2}
        delta = {"modified": {"a": 10}}
        result = apply_delta(base, delta)
        assert result == {"a": 10, "b": 2}

    def test_all_operations_combined(self) -> None:
        base = {"keep": "yes", "change": "old", "drop": "bye"}
        delta: dict[str, object] = {
            "added": {"new": "hello"},
            "removed": ["drop"],
            "modified": {"change": "new"},
        }
        result = apply_delta(base, delta)
        assert result == {"keep": "yes", "change": "new", "new": "hello"}

    def test_remove_nonexistent_key_is_safe(self) -> None:
        base = {"a": 1}
        delta = {"removed": ["nonexistent"]}
        result = apply_delta(base, delta)
        assert result == {"a": 1}

    def test_base_not_mutated(self) -> None:
        base = {"a": 1}
        delta = {"added": {"b": 2}}
        apply_delta(base, delta)
        assert "b" not in base

    def test_non_dict_added_ignored(self) -> None:
        """If 'added' is not a dict, it should be ignored."""
        base = {"a": 1}
        delta = {"added": "not_a_dict"}
        result = apply_delta(base, delta)
        assert result == {"a": 1}

    def test_non_list_removed_ignored(self) -> None:
        """If 'removed' is not a list, it should be ignored."""
        base = {"a": 1}
        delta = {"removed": "not_a_list"}
        result = apply_delta(base, delta)
        assert result == {"a": 1}

    def test_non_dict_modified_ignored(self) -> None:
        """If 'modified' is not a dict, it should be ignored."""
        base = {"a": 1}
        delta = {"modified": "not_a_dict"}
        result = apply_delta(base, delta)
        assert result == {"a": 1}
