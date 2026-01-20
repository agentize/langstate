"""Pydantic schemas for base State module.

This module contains all data models used by the State interface.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class ValueConfidence(BaseModel):
    """Value with associated confidence score.

    Attributes:
        value: The actual value
        confidence: Confidence score (0.0 to 1.0)
    """

    value: object
    confidence: float = 0.0

    model_config = ConfigDict(extra="allow")


class Inference(BaseModel):
    """Inference step that led to a value.

    Attributes:
        content: Description of the inference/reasoning
        mutator_id: Identifier of the mutator that generated this inference
        timestamp: Optional timestamp when inference was made
    """

    content: str
    mutator_id: str = "unknown"
    timestamp: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class FieldState(BaseModel):
    """Base state for a single field.

    Attributes:
        field_id: Unique identifier for the field
        metadata: Additional field metadata
    """

    field_id: str
    metadata: Dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")
