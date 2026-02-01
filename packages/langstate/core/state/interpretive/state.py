"""Interpretive State implementation using DAH storage."""

from typing import Optional

from core.state.base.state import State
from core.state.interpretive.base import BaseInterpretiveState
from core.state.interpretive.schema import (
    Inference,
    InterpretiveFieldState,
    ValueConfidence,
)


class InterpretiveState(State[InterpretiveFieldState], BaseInterpretiveState):
    """Interpretive State implementation with DAH-based storage and inference tracking.

    Implements BaseInterpretiveState interface using InterpretiveFieldState as node values.
    Field values are stored directly in DAH nodes with paths like:
    - "name" for simple fields
    - "address.city" for nested objects
    - "guests.0.email" for array elements

    Values are InterpretiveFieldState objects with:
    - inference: List of inferences about the field
    - values: List of value-confidence pairs
    """

    def _is_field_filled(self, value: Optional[InterpretiveFieldState]) -> bool:
        """Check if a field value is considered filled.

        Args:
            value: The field value to check

        Returns:
            True if the field has values
        """
        if value is None:
            return False
        return len(value.values) > 0

    def copy(self) -> "InterpretiveState":
        """Create a deep copy of the state.

        Returns:
            A new InterpretiveState instance with deep copied data
        """
        new_state = InterpretiveState()

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

    def add_inference(self, path: str, inference: Inference) -> None:
        """Add an inference to a field.

        Args:
            path: The field path (e.g., "name" or "guests.0.email")
            inference: The inference to add
        """
        field_state = self._get_or_create_field_state(path)
        field_state.inference.append(inference)

    def add_value(self, path: str, value_confidence: ValueConfidence) -> None:
        """Add a value-confidence pair to a field.

        Args:
            path: The field path (e.g., "name" or "guests.0.email")
            value_confidence: The value with confidence
        """
        field_state = self._get_or_create_field_state(path)
        field_state.values.append(value_confidence)

    def get_best_value(self, path: str) -> Optional[ValueConfidence]:
        """Get the value with highest confidence for a field.

        Args:
            path: The field path (e.g., "name" or "guests.0.email")

        Returns:
            ValueConfidence with highest confidence, None if no values
        """
        value = self.get_field(path)
        if value is None:
            return None
        if not value.values:
            return None

        return max(value.values, key=lambda vc: vc.confidence)

    def _get_or_create_field_state(self, path: str) -> InterpretiveFieldState:
        """Get or create field state for a field path.

        Args:
            path: The field path

        Returns:
            The InterpretiveFieldState for this field
        """
        value = self.get_field(path)

        if value is not None:
            return value

        # Create new field state
        new_field_state = InterpretiveFieldState(inference=[], values=[])
        self.set_field(path, new_field_state)

        return new_field_state
