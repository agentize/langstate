"""Interpretive State implementation for LangState.

The Interpretive State represents the reasoning process with inferences and confidence scores.
Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}

This state tracks how values were derived and maintains multiple candidate values.
"""

from typing import Dict, List, Optional

from ..base.state import BaseState
from ..base.schema import Inference, ValueConfidence
from .schema import InterpretiveFieldState, InterpretiveStateData


class InterpretiveState(BaseState):
    """Interpretive State implementation.

    The Interpretive State stores field values with inference chains and confidence scores.
    This is the state used during conversation to track reasoning and multiple candidates.

    Format:
        {
            field_id: {
                inference: [{content, mutator_id, timestamp}],
                values: [{value, confidence}]
            }
        }

    Example:
        state = InterpretiveState()

        # Add inference and value
        state.add_inference("name", Inference(
            content="User said 'my name is John'",
            mutator_id="llm_mutator"
        ))
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))
        state.add_value("name", ValueConfidence(value="Jon", confidence=0.3))

        # Get best value
        best = state.get_best_value("name")  # ValueConfidence(value="John", confidence=0.9)
    """

    def __init__(self, initial_data: Optional[Dict[str, object]] = None) -> None:
        """Initialize interpretive state.

        Args:
            initial_data: Optional initial field data
        """
        self._data = InterpretiveStateData()
        if initial_data:
            for field_id, field_data in initial_data.items():
                self._initialize_field_from_data(field_id, field_data)

    def _initialize_field_from_data(self, field_id: str, field_data: object) -> None:
        """Initialize a field from data dictionary.

        Args:
            field_id: The field identifier
            field_data: The field data (dict with inference/values or simple value)
        """
        if isinstance(field_data, dict):
            inference_list = [
                Inference(**inf) if isinstance(inf, dict) else inf
                for inf in field_data.get("inference", [])
            ]
            values_list = [
                ValueConfidence(**val) if isinstance(val, dict) else val
                for val in field_data.get("values", [])
            ]
            self._data.fields[field_id] = InterpretiveFieldState(
                field_id=field_id,
                inference=inference_list,
                values=values_list,
                metadata=field_data.get("metadata", {}),
            )
        else:
            # Simple value - wrap with default confidence
            self._data.fields[field_id] = InterpretiveFieldState(
                field_id=field_id,
                values=[ValueConfidence(value=field_data, confidence=0.0)],
            )

    def get_field(self, field_id: str) -> Optional[InterpretiveFieldState]:
        """Get the full state for a specific field.

        Args:
            field_id: The field identifier

        Returns:
            InterpretiveFieldState, None if not found
        """
        return self._data.fields.get(field_id)

    def set_field(self, field_id: str, value: object) -> None:
        """Set the value for a specific field.

        For interpretive state, this creates/updates the field with the given data.

        Args:
            field_id: The field identifier
            value: The value (can be InterpretiveFieldState or dict or simple value)
        """
        if isinstance(value, InterpretiveFieldState):
            self._data.fields[field_id] = value
        elif isinstance(value, dict):
            self._initialize_field_from_data(field_id, value)
        else:
            # Simple value - wrap with default confidence
            self._data.fields[field_id] = InterpretiveFieldState(
                field_id=field_id, values=[ValueConfidence(value=value, confidence=0.0)]
            )

    def add_inference(self, field_id: str, inference: Inference) -> None:
        """Add an inference to a field.

        Args:
            field_id: The field identifier
            inference: The inference to add
        """
        if field_id not in self._data.fields:
            self._data.fields[field_id] = InterpretiveFieldState(field_id=field_id)
        self._data.fields[field_id].inference.append(inference)

    def add_value(self, field_id: str, value_confidence: ValueConfidence) -> None:
        """Add a value-confidence pair to a field.

        Args:
            field_id: The field identifier
            value_confidence: The value with confidence
        """
        if field_id not in self._data.fields:
            self._data.fields[field_id] = InterpretiveFieldState(field_id=field_id)
        self._data.fields[field_id].values.append(value_confidence)

    def get_best_value(self, field_id: str) -> Optional[ValueConfidence]:
        """Get the value with highest confidence for a field.

        Args:
            field_id: The field identifier

        Returns:
            ValueConfidence with highest confidence, None if no values
        """
        field_state = self._data.fields.get(field_id)
        if not field_state or not field_state.values:
            return None
        return max(field_state.values, key=lambda x: x.confidence)

    def get_all_fields(self) -> Dict[str, InterpretiveFieldState]:
        """Get all fields and their states.

        Returns:
            Dictionary of field_id to InterpretiveFieldState
        """
        return dict(self._data.fields)

    def get_filled_fields(self) -> List[str]:
        """Get list of fields that have values.

        Returns:
            List of field identifiers that have at least one value
        """
        return [
            field_id
            for field_id, field_state in self._data.fields.items()
            if field_state.values
        ]

    def get_empty_fields(self) -> List[str]:
        """Get list of fields that have no values.

        Returns:
            List of field identifiers that have no values
        """
        return [
            field_id
            for field_id, field_state in self._data.fields.items()
            if not field_state.values
        ]

    def is_complete(
        self, required_fields: Optional[List[str]] = None, min_confidence: float = 0.0
    ) -> bool:
        """Check if the state is complete.

        Args:
            required_fields: Optional list of required field IDs.
                If None, checks all fields.
            min_confidence: Minimum confidence threshold for a value to count

        Returns:
            True if all required fields have values above threshold
        """
        fields_to_check = required_fields or list(self._data.fields.keys())
        for field_id in fields_to_check:
            field_state = self._data.fields.get(field_id)
            if not field_state or not field_state.values:
                return False
            best_value = max(field_state.values, key=lambda x: x.confidence)
            if best_value.confidence < min_confidence:
                return False
        return True

    def copy(self) -> "InterpretiveState":
        """Create a copy of the state.

        Returns:
            A new InterpretiveState instance with copied data
        """
        new_state = InterpretiveState()
        for field_id, field_state in self._data.fields.items():
            new_state._data.fields[field_id] = InterpretiveFieldState(
                field_id=field_id,
                inference=list(field_state.inference),
                values=list(field_state.values),
                metadata=dict(field_state.metadata),
            )
        new_state._data.metadata = dict(self._data.metadata)
        return new_state

    def to_dict(self) -> Dict[str, object]:
        """Convert state to dictionary representation.

        Returns:
            Dictionary in interpretive state format
        """
        return {
            field_id: {
                "inference": [
                    {
                        "content": inf.content,
                        "mutator_id": inf.mutator_id,
                        "timestamp": inf.timestamp,
                    }
                    for inf in field_state.inference
                ],
                "values": [
                    {"value": val.value, "confidence": val.confidence}
                    for val in field_state.values
                ],
            }
            for field_id, field_state in self._data.fields.items()
        }

    def to_canonical_dict(self) -> Dict[str, object]:
        """Convert to canonical state format (best values only).

        Returns:
            Dictionary in canonical format {field_id: value}
        """
        result: Dict[str, object] = {}
        for field_id in self._data.fields:
            best = self.get_best_value(field_id)
            if best:
                result[field_id] = best.value
        return result
