
from typing import Dict, List, Optional

from packages.langstate.core.state.interpretive.base import BaseInterpretiveState
from packages.langstate.core.state.interpretive.schema import (
    Inference,
    InterpretiveFieldState,
    InterpretiveStateSchema,
    ValueConfidence,
)


class InterpretiveState(BaseInterpretiveState):
    """Interpretive State implementation with inference tracking and confidence scores.
    
    Implements BaseInterpretiveState interface using InterpretiveFieldState internally.
    """

    def __init__(self) -> None:
        """Initialize the interpretive state with empty field states."""
        self._fields: Dict[str, InterpretiveFieldState] = {}

    def get_field(self, field_id: str) -> Optional[InterpretiveStateSchema]:
        """Get the value/data for a specific field.

        Args:
            field_id: The field identifier

        Returns:
            Field state wrapped in InterpretiveStateSchema, None if not found
        """
        field_state = self._fields.get(field_id)
        if field_state is None:
            return None
        # Wrap single field in schema format
        return InterpretiveStateSchema({field_id: field_state})

    def set_field(self, field_id: str, value: InterpretiveStateSchema) -> None:
        """Set the value/data for a specific field.

        Args:
            field_id: The field identifier
            value: The value or data to set (InterpretiveStateSchema)
        """
        # Extract field state from schema
        if field_id in value.root:
            self._fields[field_id] = value.root[field_id]

    def get_all_fields(self) -> Dict[str, InterpretiveStateSchema]:
        """Get all fields and their values/data.

        Returns:
            Dictionary of field_id to InterpretiveStateSchema
        """
        return {
            field_id: InterpretiveStateSchema({field_id: field_state})
            for field_id, field_state in self._fields.items()
        }

    def get_filled_fields(self) -> List[str]:
        """Get list of fields that have been filled.

        Returns:
            List of field identifiers that have values
        """
        return [
            field_id for field_id, field_state in self._fields.items()
            if field_state.values
        ]

    def get_empty_fields(self) -> List[str]:
        """Get list of fields that are still empty.

        Returns:
            List of field identifiers that don't have values
        """
        return [
            field_id for field_id, field_state in self._fields.items()
            if not field_state.values
        ]

    def is_complete(self, required_fields: Optional[List[str]] = None) -> bool:
        """Check if the state is complete.

        Args:
            required_fields: Optional list of required field IDs.
                If None, checks all fields.

        Returns:
            True if all required fields have values
        """
        fields_to_check = required_fields if required_fields is not None else list(self._fields.keys())
        
        for field_id in fields_to_check:
            field_state = self._fields.get(field_id)
            if not field_state or not field_state.values:
                return False
        
        return True

    def copy(self) -> "InterpretiveState":
        """Create a copy of the state.

        Returns:
            A new InterpretiveState instance with copied data
        """
        new_state = InterpretiveState()
        # Deep copy field states
        for field_id, field_state in self._fields.items():
            new_state._fields[field_id] = field_state.model_copy(deep=True)
        return new_state

    def to_dict(self) -> Dict[str, object]:
        """Convert state to dictionary representation.

        Returns:
            Dictionary representation of the state
        """
        return {
            field_id: field_state.model_dump()
            for field_id, field_state in self._fields.items()
        }

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
        field_state = self._fields.get(field_id)
        if not field_state or not field_state.values:
            return None
        
        return max(field_state.values, key=lambda vc: vc.confidence)

    def to_canonical_dict(self) -> Dict[str, object]:
        """Convert to canonical state format (best values only).

        Returns:
            Dictionary in canonical format {field_id: value}
        """
        result: Dict[str, object] = {}
        for field_id in self._fields.keys():
            best_value = self.get_best_value(field_id)
            if best_value is not None:
                result[field_id] = best_value.value
        return result

    def _get_or_create_field_state(self, field_id: str) -> InterpretiveFieldState:
        """Get or create field state for a field ID.

        Args:
            field_id: The field identifier

        Returns:
            The field state for this field
        """
        if field_id not in self._fields:
            self._fields[field_id] = InterpretiveFieldState(inference=[], values=[])
        return self._fields[field_id]