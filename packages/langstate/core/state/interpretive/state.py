"""Interpretive State interface for LangState.

The Interpretive State represents the reasoning process with inferences and confidence scores.
Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}

This state tracks how values were derived and maintains multiple candidate values.
"""

from abc import abstractmethod
from typing import Dict, List, Optional

from ..base.state import BaseState
from ..base.schema import Inference, ValueConfidence
from .schema import InterpretiveFieldState


class InterpretiveState(BaseState):
    """Interpretive State interface.

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
        state = InterpretiveStateImpl()

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

    @abstractmethod
    def get_field(self, field_id: str) -> Optional[InterpretiveFieldState]:
        """Get the full state for a specific field.

        Args:
            field_id: The field identifier

        Returns:
            InterpretiveFieldState, None if not found
        """
        pass

    @abstractmethod
    def set_field(self, field_id: str, value: object) -> None:
        """Set the value for a specific field.

        For interpretive state, this creates/updates the field with the given data.

        Args:
            field_id: The field identifier
            value: The value (can be InterpretiveFieldState or dict or simple value)
        """
        pass

    @abstractmethod
    def add_inference(self, field_id: str, inference: Inference) -> None:
        """Add an inference to a field.

        Args:
            field_id: The field identifier
            inference: The inference to add
        """
        pass

    @abstractmethod
    def add_value(self, field_id: str, value_confidence: ValueConfidence) -> None:
        """Add a value-confidence pair to a field.

        Args:
            field_id: The field identifier
            value_confidence: The value with confidence
        """
        pass

    @abstractmethod
    def get_best_value(self, field_id: str) -> Optional[ValueConfidence]:
        """Get the value with highest confidence for a field.

        Args:
            field_id: The field identifier

        Returns:
            ValueConfidence with highest confidence, None if no values
        """
        pass

    @abstractmethod
    def get_all_fields(self) -> Dict[str, InterpretiveFieldState]:
        """Get all fields and their states.

        Returns:
            Dictionary of field_id to InterpretiveFieldState
        """
        pass

    @abstractmethod
    def get_filled_fields(self) -> List[str]:
        """Get list of fields that have values.

        Returns:
            List of field identifiers that have at least one value
        """
        pass

    @abstractmethod
    def get_empty_fields(self) -> List[str]:
        """Get list of fields that have no values.

        Returns:
            List of field identifiers that have no values
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def copy(self) -> "InterpretiveState":
        """Create a copy of the state.

        Returns:
            A new InterpretiveState instance with copied data
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, object]:
        """Convert state to dictionary representation.

        Returns:
            Dictionary in interpretive state format
        """
        pass

    @abstractmethod
    def to_canonical_dict(self) -> Dict[str, object]:
        """Convert to canonical state format (best values only).

        Returns:
            Dictionary in canonical format {field_id: value}
        """
        pass
