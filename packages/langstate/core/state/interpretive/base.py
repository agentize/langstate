"""Interpretive State interface for LangState.

The Interpretive State represents the reasoning process with inferences and confidence scores.
Format: {key: {inference: {content, mutator_id, message_id} | null, values: [{value, confidence}]}}

This state tracks how values were derived and maintains multiple candidate values.
Uses DAH for internal storage with field paths as node identifiers.
"""

from abc import abstractmethod
from typing import Any, Optional

from pydantic_core import core_schema

from ..base.base import BaseState
from .schema import ValueConfidence
from .schema import Inference, InterpretiveFieldState


class BaseInterpretiveState(BaseState[InterpretiveFieldState]):
    """Interpretive State interface.

    The Interpretive State stores field values with optional inference and confidence scores.
    This is the state used during conversation to track reasoning and multiple candidates.
    Uses DAH internally with path-based field addressing.

    Format:
        {
            field_path: {
                inference: {content, mutator_id, message_id} | null,
                values: [{value, confidence}]
            }
        }

    Example:
        state = InterpretiveStateImpl()

        # Add inference and value
        state.add_inference("name", Inference(
            content="User said 'my name is John'",
            mutator_id="llm_mutator",
            message_id="msg_123"
        ))
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))
        state.add_value("name", ValueConfidence(value="Jon", confidence=0.3))

        # Nested array element
        state.add_value("guests.0.name", ValueConfidence(value="Jane", confidence=0.95))

        # Get best value
        best = state.get_best_value("name")  # ValueConfidence(value="John", confidence=0.9)
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Any,
    ) -> core_schema.CoreSchema:
        """Generate Pydantic core schema for BaseInterpretiveState.

        Returns an is-instance schema that validates the value is an instance
        of BaseInterpretiveState without inspecting its generic type parameters.
        """
        return core_schema.is_instance_schema(cls)

    @abstractmethod
    def add_inference(self, path: str, inference: Inference) -> None:
        """Add an inference to a field.

        Args:
            path: The field path (e.g., "name" or "guests.0.email")
            inference: The inference to add
        """
        pass

    @abstractmethod
    def add_value(self, path: str, value_confidence: ValueConfidence) -> None:
        """Add a value-confidence pair to a field.

        Args:
            path: The field path (e.g., "name" or "guests.0.email")
            value_confidence: The value with confidence
        """
        pass

    @abstractmethod
    def get_best_value(self, path: str) -> Optional[ValueConfidence]:
        """Get the value with highest confidence for a field.

        Args:
            path: The field path (e.g., "name" or "guests.0.email")

        Returns:
            ValueConfidence with highest confidence, None if no values
        """
        pass
