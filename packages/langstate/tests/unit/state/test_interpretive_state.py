"""Unit tests for InterpretiveState implementation.

Tests the InterpretiveState class with DAH-based storage,
inference tracking, and value-confidence pairs.
"""

# pyright: reportPrivateUsage=false

from core.state.interpretive.schema import (
    Inference,
    InterpretiveFieldState,
    ValueConfidence,
)
from core.state.interpretive.state import InterpretiveState


class TestInterpretiveStateInitialization:
    """Tests for InterpretiveState initialization."""

    def test_init_creates_empty_state(self) -> None:
        """InterpretiveState should initialize empty."""
        state = InterpretiveState()

        assert len(state.get_all_fields()) == 0

    def test_instance_type(self) -> None:
        """InterpretiveState should be correct type."""
        state = InterpretiveState()

        assert isinstance(state, InterpretiveState)


class TestInterpretiveStateAddValue:
    """Tests for add_value operation."""

    def test_add_value_new_field(self) -> None:
        """add_value should create field if it doesn't exist."""
        state = InterpretiveState()

        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        field_state = state.get_field("name")
        assert field_state is not None
        assert len(field_state.values) == 1
        assert field_state.values[0].value == "John"
        assert field_state.values[0].confidence == 0.9

    def test_add_value_existing_field(self) -> None:
        """add_value should append to existing field."""
        state = InterpretiveState()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        state.add_value("name", ValueConfidence(value="Jon", confidence=0.7))

        field_state = state.get_field("name")
        assert field_state is not None
        assert len(field_state.values) == 2

    def test_add_value_multiple_fields(self) -> None:
        """add_value should work with multiple fields."""
        state = InterpretiveState()

        state.add_value("name", ValueConfidence(value="John", confidence=0.9))
        state.add_value(
            "email", ValueConfidence(value="john@test.com", confidence=0.85)
        )

        assert state.get_field("name") is not None
        assert state.get_field("email") is not None


class TestInterpretiveStateAddInference:
    """Tests for add_inference operation."""

    def test_add_inference_new_field(self) -> None:
        """add_inference should create field if it doesn't exist."""
        state = InterpretiveState()
        inference = Inference(content="User said 'my name is John'", mutator_id="llm")

        state.add_inference("name", inference)

        field_state = state.get_field("name")
        assert field_state is not None
        assert len(field_state.inference) == 1
        assert field_state.inference[0].content == "User said 'my name is John'"
        assert field_state.inference[0].mutator_id == "llm"

    def test_add_inference_existing_field(self) -> None:
        """add_inference should append to existing field."""
        state = InterpretiveState()
        state.add_inference(
            "name", Inference(content="First inference", mutator_id="llm1")
        )

        state.add_inference(
            "name", Inference(content="Second inference", mutator_id="llm2")
        )

        field_state = state.get_field("name")
        assert field_state is not None
        assert len(field_state.inference) == 2

    def test_add_inference_with_default_mutator_id(self) -> None:
        """add_inference should use default mutator_id."""
        state = InterpretiveState()
        inference = Inference(content="Some inference", mutator_id="unknown")

        state.add_inference("name", inference)

        field_state = state.get_field("name")
        assert field_state is not None
        assert field_state.inference[0].mutator_id == "unknown"


class TestInterpretiveStateGetBestValue:
    """Tests for get_best_value operation."""

    def test_get_best_value_single_value(self) -> None:
        """get_best_value should return only value."""
        state = InterpretiveState()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        best = state.get_best_value("name")

        assert best is not None
        assert best.value == "John"
        assert best.confidence == 0.9

    def test_get_best_value_multiple_values(self) -> None:
        """get_best_value should return highest confidence."""
        state = InterpretiveState()
        state.add_value("name", ValueConfidence(value="John", confidence=0.6))
        state.add_value("name", ValueConfidence(value="Jonathan", confidence=0.9))
        state.add_value("name", ValueConfidence(value="Jon", confidence=0.3))

        best = state.get_best_value("name")

        assert best is not None
        assert best.value == "Jonathan"
        assert best.confidence == 0.9

    def test_get_best_value_nonexistent_field(self) -> None:
        """get_best_value should return None for non-existent field."""
        state = InterpretiveState()

        best = state.get_best_value("nonexistent")

        assert best is None

    def test_get_best_value_empty_values(self) -> None:
        """get_best_value should return None for field with no values."""
        state = InterpretiveState()
        # Create field with inference but no values
        state.add_inference("name", Inference(content="test", mutator_id="llm"))

        best = state.get_best_value("name")

        assert best is None


class TestInterpretiveStateNestedPaths:
    """Tests for nested path handling."""

    def test_nested_object_path(self) -> None:
        """Should handle nested object paths."""
        state = InterpretiveState()

        state.add_value("address.city", ValueConfidence(value="NYC", confidence=0.95))
        state.add_value(
            "address.country", ValueConfidence(value="USA", confidence=0.98)
        )

        city_best = state.get_best_value("address.city")
        country_best = state.get_best_value("address.country")

        assert city_best is not None
        assert city_best.value == "NYC"
        assert country_best is not None
        assert country_best.value == "USA"

    def test_array_element_path(self) -> None:
        """Should handle array element paths."""
        state = InterpretiveState()

        state.add_value("guests.0.name", ValueConfidence(value="Alice", confidence=0.9))
        state.add_value("guests.1.name", ValueConfidence(value="Bob", confidence=0.85))

        guest0 = state.get_best_value("guests.0.name")
        guest1 = state.get_best_value("guests.1.name")

        assert guest0 is not None
        assert guest0.value == "Alice"
        assert guest1 is not None
        assert guest1.value == "Bob"


class TestInterpretiveStateCopy:
    """Tests for copy operation."""

    def test_copy_returns_interpretive_state(self) -> None:
        """copy should return InterpretiveState instance."""
        state = InterpretiveState()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        copied = state.copy()

        assert isinstance(copied, InterpretiveState)

    def test_copy_preserves_values(self) -> None:
        """copy should preserve all values."""
        state = InterpretiveState()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))
        state.add_value("name", ValueConfidence(value="Jon", confidence=0.6))

        copied = state.copy()

        field_state = copied.get_field("name")
        assert field_state is not None
        assert len(field_state.values) == 2

    def test_copy_preserves_inferences(self) -> None:
        """copy should preserve all inferences."""
        state = InterpretiveState()
        state.add_inference("name", Inference(content="inference1", mutator_id="llm"))
        state.add_inference("name", Inference(content="inference2", mutator_id="llm"))

        copied = state.copy()

        field_state = copied.get_field("name")
        assert field_state is not None
        assert len(field_state.inference) == 2

    def test_copy_is_deep(self) -> None:
        """copy should be a deep copy."""
        state = InterpretiveState()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        copied = state.copy()
        copied.add_value("name", ValueConfidence(value="NewValue", confidence=0.5))

        original_field = state.get_field("name")
        copied_field = copied.get_field("name")

        assert original_field is not None
        assert copied_field is not None
        assert len(original_field.values) == 1
        assert len(copied_field.values) == 2

    def test_copy_preserves_dependencies(self) -> None:
        """copy should preserve field dependencies."""
        state = InterpretiveState()
        state.add_value("parent", ValueConfidence(value="p", confidence=1.0))
        state.add_value("child", ValueConfidence(value="c", confidence=1.0))
        state.add_field_dependency("parent", "child")

        copied = state.copy()

        children = copied.get_children("parent")
        assert "child" in children

    def test_copy_skips_none_values(self) -> None:
        """copy should skip None field values."""
        state = InterpretiveState()
        state.add_value("valid", ValueConfidence(value="test", confidence=1.0))
        # Set a field to None directly (edge case)
        state.set_field("empty", None)  # type: ignore[arg-type]

        copied = state.copy()

        # Valid field should be copied
        assert copied.get_field("valid") is not None
        # None field should be skipped in copy
        assert copied.get_field("empty") is None

    def test_copy_handles_nested_structure(self) -> None:
        """copy should handle nested structure with hyperedges."""
        state = InterpretiveState()
        state.add_value("a.b.c", ValueConfidence(value="deep", confidence=0.9))

        copied = state.copy()

        best = copied.get_best_value("a.b.c")
        assert best is not None
        assert best.value == "deep"


class TestInterpretiveStateIsFieldFilled:
    """Tests for _is_field_filled in InterpretiveState."""

    def test_is_field_filled_with_values(self) -> None:
        """Field with values should be considered filled."""
        state = InterpretiveState()
        field_state = InterpretiveFieldState(
            inference=[], values=[ValueConfidence(value="test", confidence=0.9)]
        )

        assert state._is_field_filled(field_state) is True

    def test_is_field_filled_empty_values(self) -> None:
        """Field with no values should not be considered filled."""
        state = InterpretiveState()
        field_state = InterpretiveFieldState(inference=[], values=[])

        assert state._is_field_filled(field_state) is False

    def test_is_field_filled_with_inference_only(self) -> None:
        """Field with only inference (no values) should not be filled."""
        state = InterpretiveState()
        field_state = InterpretiveFieldState(
            inference=[Inference(content="test", mutator_id="llm")], values=[]
        )

        assert state._is_field_filled(field_state) is False

    def test_is_field_filled_none(self) -> None:
        """None field should not be considered filled."""
        state = InterpretiveState()

        assert state._is_field_filled(None) is False


class TestInterpretiveStateFilledEmptyFields:
    """Tests for get_filled_fields and get_empty_fields."""

    def test_get_filled_fields(self) -> None:
        """Should return only filled field paths."""
        state = InterpretiveState()
        state.add_value("filled", ValueConfidence(value="test", confidence=0.9))
        state.add_inference("empty", Inference(content="test", mutator_id="llm"))

        filled = state.get_filled_fields()

        assert "filled" in filled
        assert "empty" not in filled

    def test_get_empty_fields(self) -> None:
        """Should return only empty field paths."""
        state = InterpretiveState()
        state.add_value("filled", ValueConfidence(value="test", confidence=0.9))
        state.add_inference("empty", Inference(content="test", mutator_id="llm"))

        empty = state.get_empty_fields()

        assert "empty" in empty
        assert "filled" not in empty


class TestInterpretiveStateIsComplete:
    """Tests for is_complete in InterpretiveState."""

    def test_is_complete_all_filled(self) -> None:
        """Should be complete when all required fields have values."""
        state = InterpretiveState()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))
        state.add_value("email", ValueConfidence(value="john@test.com", confidence=0.9))

        result = state.is_complete(required_fields=["name", "email"])

        assert result is True

    def test_is_complete_missing_required(self) -> None:
        """Should be incomplete when required field is missing."""
        state = InterpretiveState()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        result = state.is_complete(required_fields=["name", "email"])

        assert result is False

    def test_is_complete_no_values_in_required(self) -> None:
        """Should be incomplete when required field has no values."""
        state = InterpretiveState()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))
        state.add_inference("email", Inference(content="test", mutator_id="llm"))

        result = state.is_complete(required_fields=["name", "email"])

        assert result is False


class TestInterpretiveStateGetOrCreateFieldState:
    """Tests for _get_or_create_field_state method."""

    def test_get_or_create_returns_existing(self) -> None:
        """Should return existing field state."""
        state = InterpretiveState()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        field_state = state._get_or_create_field_state("name")

        assert len(field_state.values) == 1

    def test_get_or_create_creates_new(self) -> None:
        """Should create new field state if not exists."""
        state = InterpretiveState()

        field_state = state._get_or_create_field_state("new_field")

        assert isinstance(field_state, InterpretiveFieldState)
        assert len(field_state.inference) == 0
        assert len(field_state.values) == 0


class TestInterpretiveStateRemoveField:
    """Tests for remove_field in InterpretiveState."""

    def test_remove_existing_field(self) -> None:
        """Should remove existing field."""
        state = InterpretiveState()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        result = state.remove_field("name")

        assert result is True
        assert state.get_field("name") is None

    def test_remove_nonexistent_field(self) -> None:
        """Should return False for non-existent field."""
        state = InterpretiveState()

        result = state.remove_field("nonexistent")

        assert result is False


class TestInterpretiveStateIterFields:
    """Tests for iter_fields in InterpretiveState."""

    def test_iter_fields_returns_all(self) -> None:
        """Should iterate over all fields."""
        state = InterpretiveState()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))
        state.add_value("email", ValueConfidence(value="john@test.com", confidence=0.8))

        fields = dict(state.iter_fields())

        assert "name" in fields
        assert "email" in fields


class TestInterpretiveStateGetAllFields:
    """Tests for get_all_fields in InterpretiveState."""

    def test_get_all_fields(self) -> None:
        """Should return all fields."""
        state = InterpretiveState()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))
        state.add_inference("email", Inference(content="test", mutator_id="llm"))

        all_fields = state.get_all_fields()

        assert "name" in all_fields
        assert "email" in all_fields


class TestInterpretiveStateEdgeCases:
    """Tests for edge cases in InterpretiveState."""

    def test_value_with_zero_confidence(self) -> None:
        """Should handle zero confidence values."""
        state = InterpretiveState()

        state.add_value("name", ValueConfidence(value="John", confidence=0.0))

        best = state.get_best_value("name")
        assert best is not None
        assert best.confidence == 0.0

    def test_value_with_none_value(self) -> None:
        """Should handle None as actual value."""
        state = InterpretiveState()

        state.add_value("optional", ValueConfidence(value=None, confidence=0.9))

        best = state.get_best_value("optional")
        assert best is not None
        assert best.value is None
        assert best.confidence == 0.9

    def test_mixed_inferences_and_values(self) -> None:
        """Should handle fields with both inferences and values."""
        state = InterpretiveState()

        state.add_inference("name", Inference(content="First hint", mutator_id="llm"))
        state.add_value("name", ValueConfidence(value="John", confidence=0.7))
        state.add_inference("name", Inference(content="Confirmed", mutator_id="llm"))
        state.add_value("name", ValueConfidence(value="John", confidence=0.95))

        field_state = state.get_field("name")
        assert field_state is not None
        assert len(field_state.inference) == 2
        assert len(field_state.values) == 2

    def test_empty_state_operations(self) -> None:
        """Should handle operations on empty state."""
        state = InterpretiveState()

        assert state.get_field("any") is None
        assert state.get_best_value("any") is None
        assert state.get_filled_fields() == []
        assert state.get_empty_fields() == []
        assert state.is_complete() is True
        assert state.get_all_fields() == {}
