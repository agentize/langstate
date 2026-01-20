"""Pydantic schemas for base State module.

This module contains all data models used by the State interface.
"""

from pydantic import BaseModel


class ValueConfidence(BaseModel):
    """Value with associated confidence score.

    Attributes:
        value: The actual value
        confidence: Confidence score (0.0 to 1.0)
    """

    value: object
    confidence: float = 0.0


class Inference(BaseModel):
    """Inference step that led to a value.

    Attributes:
        content: Description of the inference/reasoning
        mutator_id: Identifier of the mutator that generated this inference
    """

    content: str
    mutator_id: str = "unknown"
