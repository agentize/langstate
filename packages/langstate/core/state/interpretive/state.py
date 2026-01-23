"""Interpretive State interface for LangState.

The Interpretive State represents the reasoning process with inferences and confidence scores.
Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}

This state tracks how values were derived and maintains multiple candidate values.
"""

from abc import abstractmethod
from typing import Dict, Optional

from ..base.state import BaseState
from ..base.schema import Inference, ValueConfidence
from .schema import InterpretiveStateSchema


class InterpretiveState(BaseState[InterpretiveStateSchema]):
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
    def to_canonical_dict(self) -> Dict[str, object]:
        """Convert to canonical state format (best values only).

        Returns:
            Dictionary in canonical format {field_id: value}
        """
        pass
