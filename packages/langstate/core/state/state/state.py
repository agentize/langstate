"""State implementation using DAH storage."""

from typing import Any, Optional, cast
from typing_extensions import Self

from pydantic_core import core_schema

from core.state.base.state import DAHState
from core.state.state.base import BaseState
from core.state.state.schema import (
    Inference,
    InterpretiveField,
    ValueConfidence,
)


class State(DAHState[InterpretiveField], BaseState):
    """State implementation with DAH-based storage and inference tracking.

    Implements BaseState interface using InterpretiveField as node values.
    Field values are stored directly in DAH nodes with paths like:
    - "name" for simple fields
    - "address.city" for nested objects
    - "guests.0.email" for array elements

    Values are InterpretiveField objects with:
    - inference: Optional single inference about the field (latest overwrites)
    - values: List of value-confidence pairs
    """

    def _is_field_filled(self, value: Optional[InterpretiveField]) -> bool:
        """Check if a field value is considered filled.

        Args:
            value: The field value to check

        Returns:
            True if the field has values
        """
        if value is None:
            return False
        return len(value.values) > 0

    def copy(self) -> Self:
        """Create a deep copy of the state.

        Returns:
            A new State instance with deep copied data
        """
        new_state = self.__class__()

        # Copy all field values
        for path, value in self.iter_fields():
            if value is not None:
                new_state._dah.add_node(path, value.model_copy(deep=True))

        # Copy all hyperedges
        for sources, target, metadata, _edge_id in self._dah.iter_hyperedges():
            try:
                new_state._dah.add_hyperedge(
                    sources, target, metadata=metadata, check_cycle=False
                )
            except ValueError:
                pass

        return new_state

    @classmethod
    def from_json(cls, json_str: str) -> "State":
        """Create a State from a JSON string.

        Delegates to :meth:`DirectedAcyclicHypergraph.from_json` with an
        ``InterpretiveField`` value parser.
        Expects the format produced by ``to_json()`` which includes
        ``nodes`` (with ``path`` and ``value``) and ``hyperedges``.

        Args:
            json_str: JSON string representation of the state

        Returns:
            A new State instance populated from the JSON data
        """
        from core.data_structure.dah.dah import DirectedAcyclicHypergraph

        def _parse_field(raw: Any) -> InterpretiveField:
            if isinstance(raw, dict):
                return InterpretiveField.model_validate(raw)
            return InterpretiveField()

        new_state = cls()
        new_state._dah = cast(
            "DirectedAcyclicHypergraph[InterpretiveField, None]",
            DirectedAcyclicHypergraph.from_json(json_str, value_parser=_parse_field),
        )
        return new_state

    def add_inference(self, path: str, inference: Inference) -> None:
        """Add an inference to a field.

        Args:
            path: The field path (e.g., "name" or "guests.0.email")
            inference: The inference to add
        """
        field_state = self._get_or_create_field_state(path)
        field_state.inference = inference

    def add_value(self, path: str, value_confidence: ValueConfidence) -> None:
        """Add a value-confidence pair to a field.

        Args:
            path: The field path (e.g., "name" or "guests.0.email")
            value_confidence: The value with confidence
        """
        field_state = self._get_or_create_field_state(path)
        field_state.values.append(value_confidence)

    def _get_or_create_field_state(self, path: str) -> InterpretiveField:
        """Get or create field state for a field path.

        Args:
            path: The field path

        Returns:
            The InterpretiveField for this field
        """
        value = self.get_field(path)

        if value is not None:
            return value

        # Create new field state
        new_field_state = InterpretiveField(inference=None, values=[])
        self.set_field(path, new_field_state)

        return new_field_state

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        """Provide a pydantic-core schema so Pydantic can accept this custom type.

        We treat the class as an opaque instance type — pydantic will accept instances
        of `State` without attempting to generate a detailed schema.
        """
        return core_schema.is_instance_schema(cls)
