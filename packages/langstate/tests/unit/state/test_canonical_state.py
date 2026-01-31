"""Unit tests for CanonicalState implementation.

Tests the CanonicalState class with DAH-based storage and primitive values.
"""

from core.state.canonical.state import CanonicalState


class TestCanonicalStateInitialization:
    """Tests for CanonicalState initialization."""

    def test_init_creates_empty_state(self) -> None:
        """CanonicalState should initialize empty."""
        state = CanonicalState()

        assert len(state.get_all_fields()) == 0

    def test_instance_type(self) -> None:
        """CanonicalState should be correct type."""
        state = CanonicalState()

        assert isinstance(state, CanonicalState)


class TestCanonicalStateFieldOperations:
    """Tests for field operations in CanonicalState."""

    def test_set_and_get_string_value(self) -> None:
        """Should handle string values."""
        state = CanonicalState()

        state.set_field("name", "John Doe")

        assert state.get_field("name") == "John Doe"

    def test_set_and_get_integer_value(self) -> None:
        """Should handle integer values."""
        state = CanonicalState()

        state.set_field("age", 30)

        assert state.get_field("age") == 30

    def test_set_and_get_float_value(self) -> None:
        """Should handle float values."""
        state = CanonicalState()

        state.set_field("price", 19.99)

        assert state.get_field("price") == 19.99

    def test_set_and_get_boolean_value(self) -> None:
        """Should handle boolean values."""
        state = CanonicalState()

        state.set_field("active", True)
        state.set_field("deleted", False)

        assert state.get_field("active") is True
        assert state.get_field("deleted") is False

    def test_set_and_get_none_value(self) -> None:
        """Should handle None values."""
        state = CanonicalState()

        state.set_field("optional", None)

        assert state.get_field("optional") is None

    def test_set_and_get_list_value(self) -> None:
        """Should handle list values."""
        state = CanonicalState()
        tags = ["python", "testing"]

        state.set_field("tags", tags)

        assert state.get_field("tags") == tags


class TestCanonicalStateNestedPaths:
    """Tests for nested path handling in CanonicalState."""

    def test_nested_object_path(self) -> None:
        """Should handle nested object paths."""
        state = CanonicalState()

        state.set_field("address.city", "New York")
        state.set_field("address.country", "USA")

        assert state.get_field("address.city") == "New York"
        assert state.get_field("address.country") == "USA"

    def test_array_element_path(self) -> None:
        """Should handle array element paths."""
        state = CanonicalState()

        state.set_field("guests.0.name", "Alice")
        state.set_field("guests.0.email", "alice@test.com")
        state.set_field("guests.1.name", "Bob")

        assert state.get_field("guests.0.name") == "Alice"
        assert state.get_field("guests.0.email") == "alice@test.com"
        assert state.get_field("guests.1.name") == "Bob"

    def test_deeply_nested_path(self) -> None:
        """Should handle deeply nested paths."""
        state = CanonicalState()

        state.set_field("user.profile.address.street.number", "123")

        assert state.get_field("user.profile.address.street.number") == "123"


class TestCanonicalStateCopy:
    """Tests for CanonicalState copy operation."""

    def test_copy_returns_canonical_state(self) -> None:
        """copy should return CanonicalState instance."""
        state = CanonicalState()
        state.set_field("name", "John")

        copied = state.copy()

        assert isinstance(copied, CanonicalState)

    def test_copy_preserves_all_values(self) -> None:
        """copy should preserve all field values."""
        state = CanonicalState()
        state.set_field("name", "John")
        state.set_field("age", 30)
        state.set_field("active", True)
        state.set_field("address.city", "NYC")

        copied = state.copy()

        assert copied.get_field("name") == "John"
        assert copied.get_field("age") == 30
        assert copied.get_field("active") is True
        assert copied.get_field("address.city") == "NYC"

    def test_copy_is_deep(self) -> None:
        """copy should be a deep copy."""
        state = CanonicalState()
        state.set_field("name", "John")

        copied = state.copy()
        copied.set_field("name", "Jane")

        assert state.get_field("name") == "John"
        assert copied.get_field("name") == "Jane"

    def test_copy_preserves_dependencies(self) -> None:
        """copy should preserve field dependencies."""
        state = CanonicalState()
        state.set_field("parent", "p_val")
        state.set_field("child", "c_val")
        state.add_field_dependency("parent", "child")

        copied = state.copy()

        children = copied.get_children("parent")
        assert "child" in children

    def test_copy_handles_nested_structure(self) -> None:
        """copy should handle nested structure with hyperedges."""
        state = CanonicalState()
        state.set_field("a.b.c", "value")

        copied = state.copy()

        assert copied.get_field("a.b.c") == "value"
        # Parent hierarchy should be preserved
        assert "a.b" in copied.get_children("a")
        assert "a.b.c" in copied.get_children("a.b")


class TestCanonicalStateIsFieldFilled:
    """Tests for _is_field_filled in CanonicalState."""

    def test_is_field_filled_with_string(self) -> None:
        """String value should be considered filled."""
        state = CanonicalState()

        assert state._is_field_filled("value") is True

    def test_is_field_filled_with_empty_string(self) -> None:
        """Empty string should be considered filled."""
        state = CanonicalState()

        assert state._is_field_filled("") is True

    def test_is_field_filled_with_zero(self) -> None:
        """Zero should be considered filled."""
        state = CanonicalState()

        assert state._is_field_filled(0) is True

    def test_is_field_filled_with_false(self) -> None:
        """False should be considered filled."""
        state = CanonicalState()

        assert state._is_field_filled(False) is True

    def test_is_field_filled_with_none(self) -> None:
        """None should not be considered filled."""
        state = CanonicalState()

        assert state._is_field_filled(None) is False


class TestCanonicalStateFilledEmptyFields:
    """Tests for get_filled_fields and get_empty_fields."""

    def test_get_filled_fields(self) -> None:
        """Should return only filled field paths."""
        state = CanonicalState()
        state.set_field("name", "John")
        state.set_field("email", None)

        filled = state.get_filled_fields()

        assert "name" in filled
        assert "email" not in filled

    def test_get_empty_fields(self) -> None:
        """Should return only empty field paths."""
        state = CanonicalState()
        state.set_field("name", "John")
        state.set_field("email", None)

        empty = state.get_empty_fields()

        assert "email" in empty
        assert "name" not in empty


class TestCanonicalStateIsComplete:
    """Tests for is_complete in CanonicalState."""

    def test_is_complete_all_filled(self) -> None:
        """Should be complete when all required fields are filled."""
        state = CanonicalState()
        state.set_field("name", "John")
        state.set_field("email", "john@test.com")

        result = state.is_complete(required_fields=["name", "email"])

        assert result is True

    def test_is_complete_missing_required(self) -> None:
        """Should be incomplete when required field is missing."""
        state = CanonicalState()
        state.set_field("name", "John")

        result = state.is_complete(required_fields=["name", "email"])

        assert result is False

    def test_is_complete_none_in_required(self) -> None:
        """Should be incomplete when required field is None."""
        state = CanonicalState()
        state.set_field("name", "John")
        state.set_field("email", None)

        result = state.is_complete(required_fields=["name", "email"])

        assert result is False


class TestCanonicalStateRemoveField:
    """Tests for remove_field in CanonicalState."""

    def test_remove_existing_field(self) -> None:
        """Should remove existing field."""
        state = CanonicalState()
        state.set_field("name", "John")

        result = state.remove_field("name")

        assert result is True
        assert state.get_field("name") is None

    def test_remove_nonexistent_field(self) -> None:
        """Should return False for non-existent field."""
        state = CanonicalState()

        result = state.remove_field("nonexistent")

        assert result is False


class TestCanonicalStateIterFields:
    """Tests for iter_fields in CanonicalState."""

    def test_iter_fields_returns_all(self) -> None:
        """Should iterate over all fields."""
        state = CanonicalState()
        state.set_field("name", "John")
        state.set_field("age", 30)

        fields = dict(state.iter_fields())

        assert "name" in fields
        assert "age" in fields
        assert fields["name"] == "John"
        assert fields["age"] == 30


class TestCanonicalStateGetFieldUuid:
    """Tests for get_field_uuid in CanonicalState."""

    def test_get_uuid_existing_field(self) -> None:
        """Should return UUID for existing field."""
        state = CanonicalState()
        state.set_field("name", "John")

        uuid = state.get_field_uuid("name")

        assert uuid is not None

    def test_get_uuid_nonexistent_field(self) -> None:
        """Should return None for non-existent field."""
        state = CanonicalState()

        uuid = state.get_field_uuid("nonexistent")

        assert uuid is None


class TestCanonicalStateEdgeCases:
    """Tests for edge cases in CanonicalState."""

    def test_update_existing_field(self) -> None:
        """Should update existing field value."""
        state = CanonicalState()
        state.set_field("name", "John")

        state.set_field("name", "Jane")

        assert state.get_field("name") == "Jane"

    def test_mixed_value_types(self) -> None:
        """Should handle mixed value types."""
        state = CanonicalState()

        state.set_field("string", "text")
        state.set_field("number", 42)
        state.set_field("float", 3.14)
        state.set_field("bool", True)
        state.set_field("null", None)

        assert state.get_field("string") == "text"
        assert state.get_field("number") == 42
        assert state.get_field("float") == 3.14
        assert state.get_field("bool") is True
        assert state.get_field("null") is None

    def test_empty_state_operations(self) -> None:
        """Should handle operations on empty state."""
        state = CanonicalState()

        assert state.get_field("any") is None
        assert state.get_filled_fields() == []
        assert state.get_empty_fields() == []
        assert state.is_complete() is True
        assert state.get_all_fields() == {}
