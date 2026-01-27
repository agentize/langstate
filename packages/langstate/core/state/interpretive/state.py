
from typing import Optional

from packages.langstate.core.state.base.state import State
from packages.langstate.core.state.interpretive.base import BaseInterpretiveState
from packages.langstate.core.state.interpretive.schema import (
    Inference,
    InterpretiveFieldState,
    ValueConfidence,
)


class InterpretiveState(State[InterpretiveFieldState], BaseInterpretiveState):
    """Interpretive State implementation with inference tracking and confidence scores.
    
    Implements BaseInterpretiveState interface using InterpretiveFieldState internally.
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

    def _field_to_dict(self, value: InterpretiveFieldState) -> object:
        """Convert a field value to dictionary representation.

        Args:
            value: The field value to convert

        Returns:
            Dictionary representation of the value
        """
        return value.model_dump()

    def copy(self) -> "InterpretiveState":
        """Create a deep copy of the state.

        Returns:
            A new InterpretiveState instance with deep copied data
        """
        new_state = InterpretiveState()
        # Deep copy field states
        for field_id, field in self._data.items():
            new_state._data[field_id] = field.model_copy(deep=True)
        return new_state

    def add_inference(self, field_id: str, inference: Inference) -> None:
        """Add an inference to a field.

        Args:
            field_id: The field identifier
            inference: The inference to add
        """
        field_state = self._get_or_create_field_state(field_id)
        field_state.inference.append(inference)

    def add_value(self, field_id: str, value_confidence: ValueConfidence) -> None:
        """Add a value-confidence pair to a field.

        Args:
            field_id: The field identifier
            value_confidence: The value with confidence
        """
        field_state = self._get_or_create_field_state(field_id)
        field_state.values.append(value_confidence)

    def get_best_value(self, field_id: str) -> Optional[ValueConfidence]:
        """Get the value with highest confidence for a field.

        Args:
            field_id: The field identifier

        Returns:
            ValueConfidence with highest confidence, None if no values
        """
        field_state = self._data.get(field_id)
        if not field_state or not field_state.values:
            return None
        
        return max(field_state.values, key=lambda vc: vc.confidence)

    def _get_or_create_field_state(self, field_id: str) -> InterpretiveFieldState:
        """Get or create field state for a field ID.

        Args:
            field_id: The field identifier

        Returns:
            The field state for this field
        """
        if field_id not in self._data:
            self._data[field_id] = InterpretiveFieldState(inference=[], values=[])
        return self._data[field_id]