"""Unit tests for State implementation.

Tests the State class with DAH-based storage,
inference tracking, and value-confidence pairs.
"""

# pyright: reportPrivateUsage=false

from typing import Any

import pytest

from core.state.state.schema import (
    Inference,
    InterpretiveField,
    ValueConfidence,
)
from core.state.state.state import State


class TestStateInitialization:
    """Tests for State initialization."""

    def test_init_creates_empty_state(self) -> None:
        """State should initialize empty."""
        state = State()

        assert len(state.get_all_fields()) == 0

    def test_instance_type(self) -> None:
        """State should be correct type."""
        state = State()

        assert isinstance(state, State)


class TestStateAddValue:
    """Tests for add_value operation."""

    def test_add_value_new_field(self) -> None:
        """add_value should create field if it doesn't exist."""
        state = State()

        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        field_state = state.get_field("name")
        assert field_state is not None
        assert len(field_state.values) == 1
        assert field_state.values[0].value == "John"
        assert field_state.values[0].confidence == 0.9

    def test_add_value_existing_field(self) -> None:
        """add_value should append to existing field."""
        state = State()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        state.add_value("name", ValueConfidence(value="Jon", confidence=0.7))

        field_state = state.get_field("name")
        assert field_state is not None
        assert len(field_state.values) == 2

    def test_add_value_multiple_fields(self) -> None:
        """add_value should work with multiple fields."""
        state = State()

        state.add_value("name", ValueConfidence(value="John", confidence=0.9))
        state.add_value(
            "email", ValueConfidence(value="john@test.com", confidence=0.85)
        )

        assert state.get_field("name") is not None
        assert state.get_field("email") is not None


class TestStateAddInference:
    """Tests for add_inference operation."""

    def test_add_inference_new_field(self) -> None:
        """add_inference should create field if it doesn't exist."""
        state = State()
        inference = Inference(content="User said 'my name is John'", mutator_id="llm")

        state.add_inference("name", inference)

        field_state = state.get_field("name")
        assert field_state is not None
        assert field_state.inference is not None
        assert field_state.inference.content == "User said 'my name is John'"
        assert field_state.inference.mutator_id == "llm"

    def test_add_inference_existing_field(self) -> None:
        """add_inference should overwrite existing inference."""
        state = State()
        state.add_inference(
            "name", Inference(content="First inference", mutator_id="llm1")
        )

        state.add_inference(
            "name", Inference(content="Second inference", mutator_id="llm2")
        )

        field_state = state.get_field("name")
        assert field_state is not None
        assert field_state.inference is not None
        assert field_state.inference.content == "Second inference"
        assert field_state.inference.mutator_id == "llm2"

    def test_add_inference_with_default_mutator_id(self) -> None:
        """add_inference should use default mutator_id."""
        state = State()
        inference = Inference(content="Some inference", mutator_id="unknown")

        state.add_inference("name", inference)

        field_state = state.get_field("name")
        assert field_state is not None
        assert field_state.inference is not None
        assert field_state.inference.mutator_id == "unknown"


class TestStateNestedPaths:
    """Tests for nested path handling."""

    def test_nested_object_path(self) -> None:
        """Should handle nested object paths."""
        state = State()

        state.add_value("address.city", ValueConfidence(value="NYC", confidence=0.95))
        state.add_value(
            "address.country", ValueConfidence(value="USA", confidence=0.98)
        )

        city_field = state.get_field("address.city")
        country_field = state.get_field("address.country")

        assert city_field is not None
        assert city_field.values[0].value == "NYC"
        assert country_field is not None
        assert country_field.values[0].value == "USA"

    def test_array_element_path(self) -> None:
        """Should handle array element paths."""
        state = State()

        state.add_value("guests.0.name", ValueConfidence(value="Alice", confidence=0.9))
        state.add_value("guests.1.name", ValueConfidence(value="Bob", confidence=0.85))

        guest0 = state.get_field("guests.0.name")
        guest1 = state.get_field("guests.1.name")

        assert guest0 is not None
        assert guest0.values[0].value == "Alice"
        assert guest1 is not None
        assert guest1.values[0].value == "Bob"


class TestStateCopy:
    """Tests for copy operation."""

    def test_copy_returns_state(self) -> None:
        """copy should return State instance."""
        state = State()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        copied = state.copy()

        assert isinstance(copied, State)

    def test_copy_preserves_values(self) -> None:
        """copy should preserve all values."""
        state = State()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))
        state.add_value("name", ValueConfidence(value="Jon", confidence=0.6))

        copied = state.copy()

        field_state = copied.get_field("name")
        assert field_state is not None
        assert len(field_state.values) == 2

    def test_copy_preserves_inferences(self) -> None:
        """copy should preserve inference."""
        state = State()
        state.add_inference("name", Inference(content="inference1", mutator_id="llm"))
        state.add_inference("name", Inference(content="inference2", mutator_id="llm"))

        copied = state.copy()

        field_state = copied.get_field("name")
        assert field_state is not None
        assert field_state.inference is not None
        assert field_state.inference.content == "inference2"
        assert field_state.inference.mutator_id == "llm"

    def test_copy_is_deep(self) -> None:
        """copy should be a deep copy."""
        state = State()
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
        state = State()
        state.add_value("parent", ValueConfidence(value="p", confidence=1.0))
        state.add_value("child", ValueConfidence(value="c", confidence=1.0))
        state.add_field_dependency("parent", "child")

        copied = state.copy()

        children = copied.get_children("parent")
        assert "child" in children

    def test_copy_skips_none_values(self) -> None:
        """copy should skip None field values."""
        state = State()
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
        state = State()
        state.add_value("a.b.c", ValueConfidence(value="deep", confidence=0.9))

        copied = state.copy()

        field = copied.get_field("a.b.c")
        assert field is not None
        assert field.values[0].value == "deep"


class TestStateIsFieldFilled:
    """Tests for _is_field_filled in State."""

    def test_is_field_filled_with_values(self) -> None:
        """Field with values should be considered filled."""
        state = State()
        field_state = InterpretiveField(
            inference=None, values=[ValueConfidence(value="test", confidence=0.9)]
        )

        assert state._is_field_filled(field_state) is True

    def test_is_field_filled_empty_values(self) -> None:
        """Field with no values should not be considered filled."""
        state = State()
        field_state = InterpretiveField(inference=None, values=[])

        assert state._is_field_filled(field_state) is False

    def test_is_field_filled_with_inference_only(self) -> None:
        """Field with only inference (no values) should not be filled."""
        state = State()
        field_state = InterpretiveField(
            inference=Inference(content="test", mutator_id="llm"), values=[]
        )

        assert state._is_field_filled(field_state) is False

    def test_is_field_filled_none(self) -> None:
        """None field should not be considered filled."""
        state = State()

        assert state._is_field_filled(None) is False


class TestStateFilledEmptyFields:
    """Tests for get_filled_fields and get_empty_fields."""

    def test_get_filled_fields(self) -> None:
        """Should return only filled field paths."""
        state = State()
        state.add_value("filled", ValueConfidence(value="test", confidence=0.9))
        state.add_inference("empty", Inference(content="test", mutator_id="llm"))

        filled = state.get_filled_fields()

        assert "filled" in filled
        assert "empty" not in filled

    def test_get_empty_fields(self) -> None:
        """Should return only empty field paths."""
        state = State()
        state.add_value("filled", ValueConfidence(value="test", confidence=0.9))
        state.add_inference("empty", Inference(content="test", mutator_id="llm"))

        empty = state.get_empty_fields()

        assert "empty" in empty
        assert "filled" not in empty


class TestStateIsComplete:
    """Tests for is_complete in State."""

    def test_is_complete_all_filled(self) -> None:
        """Should be complete when all required fields have values."""
        state = State()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))
        state.add_value("email", ValueConfidence(value="john@test.com", confidence=0.9))

        result = state.is_complete(required_fields=["name", "email"])

        assert result is True

    def test_is_complete_missing_required(self) -> None:
        """Should be incomplete when required field is missing."""
        state = State()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        result = state.is_complete(required_fields=["name", "email"])

        assert result is False

    def test_is_complete_no_values_in_required(self) -> None:
        """Should be incomplete when required field has no values."""
        state = State()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))
        state.add_inference("email", Inference(content="test", mutator_id="llm"))

        result = state.is_complete(required_fields=["name", "email"])

        assert result is False


class TestStateGetOrCreateFieldState:
    """Tests for _get_or_create_field_state method."""

    def test_get_or_create_returns_existing(self) -> None:
        """Should return existing field state."""
        state = State()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        field_state = state._get_or_create_field_state("name")

        assert len(field_state.values) == 1

    def test_get_or_create_creates_new(self) -> None:
        """Should create new field state if not exists."""
        state = State()

        field_state = state._get_or_create_field_state("new_field")

        assert isinstance(field_state, InterpretiveField)
        assert field_state.inference is None
        assert len(field_state.values) == 0


class TestStateRemoveField:
    """Tests for remove_field in State."""

    def test_remove_existing_field(self) -> None:
        """Should remove existing field."""
        state = State()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        result = state.remove_field("name")

        assert result is True
        assert state.get_field("name") is None

    def test_remove_nonexistent_field(self) -> None:
        """Should return False for non-existent field."""
        state = State()

        result = state.remove_field("nonexistent")

        assert result is False


class TestStateIterFields:
    """Tests for iter_fields in State."""

    def test_iter_fields_returns_all(self) -> None:
        """Should iterate over all fields."""
        state = State()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))
        state.add_value("email", ValueConfidence(value="john@test.com", confidence=0.8))

        fields = dict(state.iter_fields())

        assert "name" in fields
        assert "email" in fields


class TestStateGetAllFields:
    """Tests for get_all_fields in State."""

    def test_get_all_fields(self) -> None:
        """Should return all fields."""
        state = State()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))
        state.add_inference("email", Inference(content="test", mutator_id="llm"))

        all_fields = state.get_all_fields()

        assert "name" in all_fields
        assert "email" in all_fields


class TestStateEdgeCases:
    """Tests for edge cases in State."""

    def test_value_with_zero_confidence(self) -> None:
        """Should handle zero confidence values."""
        state = State()

        state.add_value("name", ValueConfidence(value="John", confidence=0.0))

        field = state.get_field("name")
        assert field is not None
        assert field.values[0].confidence == 0.0

    def test_value_with_none_value(self) -> None:
        """Should handle None as actual value."""
        state = State()

        state.add_value("optional", ValueConfidence(value=None, confidence=0.9))

        field = state.get_field("optional")
        assert field is not None
        assert field.values[0].value is None
        assert field.values[0].confidence == 0.9

    def test_mixed_inferences_and_values(self) -> None:
        """Should handle fields with both inferences and values."""
        state = State()

        state.add_inference("name", Inference(content="First hint", mutator_id="llm"))
        state.add_value("name", ValueConfidence(value="John", confidence=0.7))
        state.add_inference("name", Inference(content="Confirmed", mutator_id="llm"))
        state.add_value("name", ValueConfidence(value="John", confidence=0.95))

        field_state = state.get_field("name")
        assert field_state is not None
        assert field_state.inference is not None
        assert field_state.inference.content == "Confirmed"
        assert len(field_state.values) == 2

    def test_empty_state_operations(self) -> None:
        """Should handle operations on empty state."""
        state = State()

        assert state.get_field("any") is None
        assert state.get_filled_fields() == []
        assert state.get_empty_fields() == []
        assert state.is_complete() is True
        assert state.get_all_fields() == {}


# ════════════════════════════════════════════════════════════════════
# State.from_json round-trip
# ════════════════════════════════════════════════════════════════════


class TestStateFromJson:
    """Tests for State.from_json deserialization."""

    def test_from_json_empty_state(self) -> None:
        """Empty state should round-trip through JSON."""
        state = State()
        json_str = state.to_json()
        restored = State.from_json(json_str)
        assert restored.get_all_fields() == {}

    def test_from_json_preserves_values(self) -> None:
        """Values should survive JSON round-trip."""
        state = State()
        state.add_value("name", ValueConfidence(value="Alice", confidence=0.9))
        state.add_value("email", ValueConfidence(value="a@b.com", confidence=0.8))

        json_str = state.to_json()
        restored = State.from_json(json_str)

        name_field = restored.get_field("name")
        assert name_field is not None
        assert len(name_field.values) == 1
        assert name_field.values[0].value == "Alice"

        email_field = restored.get_field("email")
        assert email_field is not None
        assert len(email_field.values) == 1

    def test_from_json_preserves_inferences(self) -> None:
        """Inferences should survive JSON round-trip."""
        state = State()
        state.add_inference("name", Inference(content="Extracted", mutator_id="m1"))
        state.add_value("name", ValueConfidence(value="Bob", confidence=0.7))

        json_str = state.to_json()
        restored = State.from_json(json_str)

        name_field = restored.get_field("name")
        assert name_field is not None
        assert name_field.inference is not None
        assert name_field.inference.content == "Extracted"
        assert name_field.inference.mutator_id == "m1"

    def test_from_json_preserves_dependencies(self) -> None:
        """Hyperedges (field dependencies) should survive JSON round-trip."""
        state = State()
        state.set_field("parent", InterpretiveField())
        state.set_field("child", InterpretiveField())
        state.add_field_dependency("parent", "child")

        json_str = state.to_json()
        restored = State.from_json(json_str)

        children = list(restored.get_children("parent"))
        assert "child" in children


# ════════════════════════════════════════════════════════════════════
# State.__get_pydantic_core_schema__
# ════════════════════════════════════════════════════════════════════


class TestStatePydanticIntegration:
    """Tests for State's pydantic-core schema hook."""

    def test_pydantic_model_with_state_field(self) -> None:
        """Pydantic model that contains a State field should work."""
        from pydantic import BaseModel

        class Container(BaseModel):
            state: State

        state = State()
        container = Container(state=state)
        assert container.state is state

    def test_pydantic_rejects_non_state(self) -> None:
        """Pydantic should reject a non-State value for a State field."""
        from pydantic import BaseModel, ValidationError

        class Container(BaseModel):
            state: State

        with pytest.raises(ValidationError):
            Container(state="not_a_state")  # type: ignore[arg-type]


# ════════════════════════════════════════════════════════════════════
# State.copy edge cases
# ════════════════════════════════════════════════════════════════════


class TestStateCopyEdgeCases:
    """Additional copy edge cases."""

    def test_copy_empty_state(self) -> None:
        """Copying an empty state should produce an empty state."""
        state = State()
        copied = state.copy()
        assert copied.get_all_fields() == {}
        assert copied is not state

    def test_copy_with_hyperedge_that_already_exists(self) -> None:
        """copy() should handle pre-existing hyperedges gracefully."""
        state = State()
        state.set_field("a", InterpretiveField())
        state.set_field("b", InterpretiveField())
        state.add_field_dependency("a", "b")

        copied = state.copy()
        children = list(copied.get_children("a"))
        assert "b" in children

    def test_copy_catches_valueerror_from_bad_hyperedge(self) -> None:
        """copy() catches ValueError when add_hyperedge fails (empty sources)."""
        from unittest.mock import patch
        from uuid import uuid4
        from core.data_structure.dah.dah import DirectedAcyclicHypergraph

        state = State()
        state.set_field("a", InterpretiveField())
        state.set_field("b", InterpretiveField())
        state.add_field_dependency("a", "b")

        original_dah = state._dah
        original_method: Any = getattr(DirectedAcyclicHypergraph, "iter_hyperedges")

        def _bad_iter(self_dah: Any) -> Any:
            yield from original_method(self_dah)
            if self_dah is original_dah:
                yield (set(), "a", None, uuid4())

        with patch.object(DirectedAcyclicHypergraph, "iter_hyperedges", _bad_iter):
            copied = state.copy()

        # Should not raise; the bad hyperedge is silently skipped
        assert copied.get_all_fields() is not None
