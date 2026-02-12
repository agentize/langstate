"""Unit tests for State base class implementation.

Tests the core State class with DAH-based storage functionality.
"""

# pyright: reportPrivateUsage=false

from uuid import UUID

import pytest

from core.state.state import State


class ConcreteState(State[str]):
    """Concrete implementation for testing the abstract State class."""

    def get_dah_nodes_count(self) -> int:
        """Get count of nodes in DAH for testing."""
        return len(self._dah.nodes)

    def has_node(self, path: str) -> bool:
        """Check if node exists in DAH for testing."""
        return self._dah.get_node(path) is not None


class TestStateInitialization:
    """Tests for State initialization."""

    def test_init_creates_empty_dah(self) -> None:
        """State should initialize with an empty DAH."""
        state = ConcreteState()

        assert state.get_dah() is not None
        assert state.get_dah_nodes_count() == 0

    def test_get_dah_returns_dah_instance(self) -> None:
        """get_dah should return the internal DAH instance."""
        state = ConcreteState()

        dah = state.get_dah()

        assert dah is not None


class TestGetSetField:
    """Tests for get_field and set_field operations."""

    def test_get_field_returns_none_for_nonexistent_path(self) -> None:
        """get_field should return None for non-existent paths."""
        state = ConcreteState()

        result = state.get_field("nonexistent")

        assert result is None

    def test_set_field_creates_new_field(self) -> None:
        """set_field should create a new field if it doesn't exist."""
        state = ConcreteState()

        state.set_field("name", "John")

        assert state.get_field("name") == "John"

    def test_set_field_updates_existing_field(self) -> None:
        """set_field should update an existing field's value."""
        state = ConcreteState()
        state.set_field("name", "John")

        state.set_field("name", "Jane")

        assert state.get_field("name") == "Jane"

    def test_set_field_with_none_value(self) -> None:
        """set_field should allow None as a value."""
        state = ConcreteState()

        state.set_field("name", None)  # type: ignore[arg-type]

        # Field exists but value is None
        assert state.has_node("name")
        assert state.get_field("name") is None

    def test_set_field_with_nested_path_creates_hierarchy(self) -> None:
        """set_field with nested path should create parent nodes."""
        state = ConcreteState()

        state.set_field("address.city", "NYC")

        assert state.get_field("address.city") == "NYC"
        # Parent node should exist
        assert state.has_node("address")

    def test_set_field_with_deeply_nested_path(self) -> None:
        """set_field should handle deeply nested paths."""
        state = ConcreteState()

        state.set_field("a.b.c.d.e", "deep_value")

        assert state.get_field("a.b.c.d.e") == "deep_value"
        # All parent nodes should exist
        assert state.has_node("a")
        assert state.has_node("a.b")
        assert state.has_node("a.b.c")
        assert state.has_node("a.b.c.d")

    def test_set_field_with_array_index_path(self) -> None:
        """set_field should handle array index paths."""
        state = ConcreteState()

        state.set_field("guests.0.name", "Alice")
        state.set_field("guests.1.name", "Bob")

        assert state.get_field("guests.0.name") == "Alice"
        assert state.get_field("guests.1.name") == "Bob"


class TestEnsureParentHierarchy:
    """Tests for _ensure_parent_hierarchy method."""

    def test_ensure_parent_hierarchy_single_level(self) -> None:
        """Single level path should not create any parents."""
        state = ConcreteState()

        state._ensure_parent_hierarchy("name")

        # No parent nodes created for single-level path
        assert state.get_dah_nodes_count() == 0

    def test_ensure_parent_hierarchy_two_levels(self) -> None:
        """Two level path should create parent node."""
        state = ConcreteState()

        state._ensure_parent_hierarchy("address.city")

        assert state.has_node("address")

    def test_ensure_parent_hierarchy_existing_parent(self) -> None:
        """Should not duplicate existing parent nodes."""
        state = ConcreteState()
        state.set_field("address.city", "NYC")

        # Creating sibling should reuse parent
        state._ensure_parent_hierarchy("address.street")

        # Note: _ensure_parent_hierarchy doesn't create the leaf
        assert state.has_node("address")


class TestRemoveField:
    """Tests for remove_field operation."""

    def test_remove_field_existing(self) -> None:
        """remove_field should return True and remove existing field."""
        state = ConcreteState()
        state.set_field("name", "John")

        result = state.remove_field("name")

        assert result is True
        assert state.get_field("name") is None

    def test_remove_field_nonexistent(self) -> None:
        """remove_field should return False for non-existent field."""
        state = ConcreteState()

        result = state.remove_field("nonexistent")

        assert result is False

    def test_remove_field_nested(self) -> None:
        """remove_field should work with nested paths."""
        state = ConcreteState()
        state.set_field("address.city", "NYC")

        result = state.remove_field("address.city")

        assert result is True
        assert state.get_field("address.city") is None


class TestGetAllFields:
    """Tests for get_all_fields operation."""

    def test_get_all_fields_empty_state(self) -> None:
        """get_all_fields should return empty dict for empty state."""
        state = ConcreteState()

        result = state.get_all_fields()

        assert result == {}

    def test_get_all_fields_with_values(self) -> None:
        """get_all_fields should return all fields with their values."""
        state = ConcreteState()
        state.set_field("name", "John")
        state.set_field("email", "john@test.com")

        result = state.get_all_fields()

        assert "name" in result
        assert "email" in result
        assert result["name"] == "John"
        assert result["email"] == "john@test.com"

    def test_get_all_fields_includes_none_values(self) -> None:
        """get_all_fields should include fields with None values."""
        state = ConcreteState()
        state.set_field("name", None)  # type: ignore[arg-type]

        result = state.get_all_fields()

        assert "name" in result
        assert result["name"] is None

    def test_get_all_fields_includes_parent_nodes(self) -> None:
        """get_all_fields should include parent container nodes."""
        state = ConcreteState()
        state.set_field("address.city", "NYC")

        result = state.get_all_fields()

        assert "address" in result  # Parent node
        assert "address.city" in result


class TestIterFields:
    """Tests for iter_fields operation."""

    def test_iter_fields_empty_state(self) -> None:
        """iter_fields should yield nothing for empty state."""
        state = ConcreteState()

        result = list(state.iter_fields())

        assert result == []

    def test_iter_fields_with_values(self) -> None:
        """iter_fields should yield all field tuples."""
        state = ConcreteState()
        state.set_field("name", "John")
        state.set_field("email", "john@test.com")

        result = dict(state.iter_fields())

        assert result["name"] == "John"
        assert result["email"] == "john@test.com"

    def test_iter_fields_includes_none_values(self) -> None:
        """iter_fields should include fields with None values."""
        state = ConcreteState()
        state.set_field("name", None)  # type: ignore[arg-type]

        result = list(state.iter_fields())

        assert ("name", None) in result


class TestGetFieldUuid:
    """Tests for get_field_uuid operation."""

    def test_get_field_uuid_existing(self) -> None:
        """get_field_uuid should return UUID for existing field."""
        state = ConcreteState()
        state.set_field("name", "John")

        result = state.get_field_uuid("name")

        assert result is not None
        assert isinstance(result, UUID)

    def test_get_field_uuid_nonexistent(self) -> None:
        """get_field_uuid should return None for non-existent field."""
        state = ConcreteState()

        result = state.get_field_uuid("nonexistent")

        assert result is None

    def test_get_field_uuid_consistency(self) -> None:
        """get_field_uuid should return same UUID for same field."""
        state = ConcreteState()
        state.set_field("name", "John")

        uuid1 = state.get_field_uuid("name")
        uuid2 = state.get_field_uuid("name")

        assert uuid1 == uuid2


class TestGetFilledFields:
    """Tests for get_filled_fields operation."""

    def test_get_filled_fields_empty_state(self) -> None:
        """get_filled_fields should return empty list for empty state."""
        state = ConcreteState()

        result = state.get_filled_fields()

        assert result == []

    def test_get_filled_fields_with_values(self) -> None:
        """get_filled_fields should return paths with values."""
        state = ConcreteState()
        state.set_field("name", "John")
        state.set_field("email", "john@test.com")

        result = state.get_filled_fields()

        assert "name" in result
        assert "email" in result

    def test_get_filled_fields_excludes_none(self) -> None:
        """get_filled_fields should exclude fields with None values."""
        state = ConcreteState()
        state.set_field("name", "John")
        state.set_field("empty", None)  # type: ignore[arg-type]

        result = state.get_filled_fields()

        assert "name" in result
        assert "empty" not in result


class TestGetEmptyFields:
    """Tests for get_empty_fields operation."""

    def test_get_empty_fields_all_filled(self) -> None:
        """get_empty_fields should return empty list when all filled."""
        state = ConcreteState()
        state.set_field("name", "John")

        result = state.get_empty_fields()

        assert "name" not in result

    def test_get_empty_fields_with_none_values(self) -> None:
        """get_empty_fields should return paths with None values."""
        state = ConcreteState()
        state.set_field("name", "John")
        state.set_field("empty", None)  # type: ignore[arg-type]

        result = state.get_empty_fields()

        assert "empty" in result
        assert "name" not in result


class TestIsComplete:
    """Tests for is_complete operation."""

    def test_is_complete_empty_state_no_requirements(self) -> None:
        """Empty state with no requirements should be complete."""
        state = ConcreteState()

        result = state.is_complete()

        assert result is True

    def test_is_complete_all_fields_filled(self) -> None:
        """State with all fields filled should be complete."""
        state = ConcreteState()
        state.set_field("name", "John")
        state.set_field("email", "john@test.com")

        result = state.is_complete()

        assert result is True

    def test_is_complete_with_required_fields_all_present(self) -> None:
        """State with all required fields filled should be complete."""
        state = ConcreteState()
        state.set_field("name", "John")
        state.set_field("email", "john@test.com")

        result = state.is_complete(required_fields=["name", "email"])

        assert result is True

    def test_is_complete_with_required_fields_missing(self) -> None:
        """State missing required fields should be incomplete."""
        state = ConcreteState()
        state.set_field("name", "John")

        result = state.is_complete(required_fields=["name", "email"])

        assert result is False

    def test_is_complete_with_none_value_required(self) -> None:
        """State with None in required field should be incomplete."""
        state = ConcreteState()
        state.set_field("name", None)  # type: ignore[arg-type]

        result = state.is_complete(required_fields=["name"])

        assert result is False

    def test_is_complete_excludes_parent_container_nodes(self) -> None:
        """is_complete should exclude parent container nodes from check."""
        state = ConcreteState()
        state.set_field("address.city", "NYC")
        # Parent "address" has None value but shouldn't fail completeness

        result = state.is_complete()

        assert result is True


class TestCopy:
    """Tests for copy operation."""

    def test_copy_creates_new_instance(self) -> None:
        """copy should create a new State instance."""
        state = ConcreteState()
        state.set_field("name", "John")

        copied = state.copy()

        assert copied is not state
        assert isinstance(copied, ConcreteState)

    def test_copy_preserves_values(self) -> None:
        """copy should preserve all field values."""
        state = ConcreteState()
        state.set_field("name", "John")
        state.set_field("address.city", "NYC")

        copied = state.copy()

        assert copied.get_field("name") == "John"
        assert copied.get_field("address.city") == "NYC"

    def test_copy_is_independent(self) -> None:
        """Changes to copy should not affect original."""
        state = ConcreteState()
        state.set_field("name", "John")

        copied = state.copy()
        copied.set_field("name", "Jane")

        assert state.get_field("name") == "John"
        assert copied.get_field("name") == "Jane"

    def test_copy_preserves_hyperedges(self) -> None:
        """copy should preserve hyperedge relationships."""
        state = ConcreteState()
        state.set_field("parent", "p_value")
        state.set_field("child", "c_value")
        state.add_field_dependency("parent", "child")

        copied = state.copy()

        children = copied.get_children("parent")
        assert "child" in children


class TestAddFieldDependency:
    """Tests for add_field_dependency operation."""

    def test_add_field_dependency_new_nodes(self) -> None:
        """add_field_dependency should create nodes if they don't exist."""
        state = ConcreteState()

        state.add_field_dependency("parent", "child")

        assert state._dah.get_node("parent") is not None
        assert state._dah.get_node("child") is not None

    def test_add_field_dependency_existing_nodes(self) -> None:
        """add_field_dependency should work with existing nodes."""
        state = ConcreteState()
        state.set_field("parent", "p_value")
        state.set_field("child", "c_value")

        state.add_field_dependency("parent", "child")

        children = state.get_children("parent")
        assert "child" in children

    def test_add_field_dependency_cycle_detection(self) -> None:
        """add_field_dependency should detect cycles."""
        state = ConcreteState()
        state.add_field_dependency("a", "b")
        state.add_field_dependency("b", "c")

        with pytest.raises(ValueError, match="[Cc]ycle"):
            state.add_field_dependency("c", "a")


class TestGetChildren:
    """Tests for get_children operation."""

    def test_get_children_no_children(self) -> None:
        """get_children should return empty list for node without children."""
        state = ConcreteState()
        state.set_field("parent", "value")

        result = state.get_children("parent")

        assert result == []

    def test_get_children_with_children(self) -> None:
        """get_children should return list of child paths."""
        state = ConcreteState()
        state.add_field_dependency("parent", "child1")
        state.add_field_dependency("parent", "child2")

        result = state.get_children("parent")

        assert "child1" in result
        assert "child2" in result

    def test_get_children_nonexistent_parent(self) -> None:
        """get_children should return empty list for non-existent parent."""
        state = ConcreteState()

        result = state.get_children("nonexistent")

        assert result == []


class TestIsFieldFilled:
    """Tests for _is_field_filled method."""

    def test_is_field_filled_with_value(self) -> None:
        """_is_field_filled should return True for non-None value."""
        state = ConcreteState()

        result = state._is_field_filled("some_value")

        assert result is True

    def test_is_field_filled_with_none(self) -> None:
        """_is_field_filled should return False for None value."""
        state = ConcreteState()

        result = state._is_field_filled(None)

        assert result is False

    def test_is_field_filled_with_empty_string(self) -> None:
        """_is_field_filled should return True for empty string."""
        state = ConcreteState()

        result = state._is_field_filled("")

        assert result is True


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_path_with_special_characters(self) -> None:
        """State should handle paths with special naming conventions."""
        state = ConcreteState()

        state.set_field("field_with_underscore", "value1")
        state.set_field("array.123.field", "value2")

        assert state.get_field("field_with_underscore") == "value1"
        assert state.get_field("array.123.field") == "value2"

    def test_multiple_siblings_at_same_level(self) -> None:
        """State should handle multiple siblings correctly."""
        state = ConcreteState()

        state.set_field("user.name", "John")
        state.set_field("user.email", "john@test.com")
        state.set_field("user.age", "30")

        assert state.get_field("user.name") == "John"
        assert state.get_field("user.email") == "john@test.com"
        assert state.get_field("user.age") == "30"

    def test_overwrite_parent_value(self) -> None:
        """Setting value on parent after child should work."""
        state = ConcreteState()
        state.set_field("address.city", "NYC")

        # Parent was created with None, now set explicit value
        state.set_field("address", "full_address")

        assert state.get_field("address") == "full_address"
        assert state.get_field("address.city") == "NYC"

    def test_hyperedge_already_exists(self) -> None:
        """Adding same dependency twice should not raise error."""
        state = ConcreteState()
        state.set_field("a.b", "value")

        # The hierarchy already creates the dependency
        # Adding it again should not raise
        state.add_field_dependency("a", "a.b")

        # Should still work
        assert "a.b" in state.get_children("a")

    def test_copy_with_hyperedge_value_error(self) -> None:
        """copy should handle ValueError in hyperedge copying gracefully."""
        state = ConcreteState()
        state.set_field("parent", "p_value")
        state.set_field("child", "c_value")
        state.add_field_dependency("parent", "child")

        # Creating a copy should work even if hyperedge already exists
        copied = state.copy()

        assert copied.get_field("parent") == "p_value"
        assert copied.get_field("child") == "c_value"

    def test_ensure_parent_hierarchy_intermediate_nodes(self) -> None:
        """Intermediate nodes should be created correctly."""
        state = ConcreteState()

        # First create a path
        state.set_field("a.b.c", "value1")

        # Then create a sibling at intermediate level
        state.set_field("a.b.d", "value2")

        # All nodes should exist
        assert state.has_node("a")
        assert state.has_node("a.b")
        assert state.has_node("a.b.c")
        assert state.has_node("a.b.d")

    def test_is_complete_with_empty_required_list(self) -> None:
        """is_complete with empty required list should be True."""
        state = ConcreteState()
        state.set_field("name", "John")

        result = state.is_complete(required_fields=[])

        assert result is True
