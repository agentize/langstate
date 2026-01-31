"""Pydantic schemas for Interpretive State module.

This module contains all data models used by the Interpretive State.
Interpretive State uses rich format with inferences and value-confidence pairs.
"""

from typing import Annotated, Dict, List

from pydantic import BaseModel, Field, RootModel


class Inference(BaseModel):
    """Inference step that led to a value."""

    content: Annotated[
        str,
        Field(description="Description of the inference/reasoning"),
    ]
    mutator_id: Annotated[
        str,
        Field(
            default="unknown",
            description="Identifier of the mutator that generated this inference",
        ),
    ]


class ValueConfidence(BaseModel):
    """Value with associated confidence score."""

    value: Annotated[
        object,
        Field(description="The actual value"),
    ]
    confidence: Annotated[
        float,
        Field(default=0.0, description="Confidence score (0.0 to 1.0)"),
    ]


class InterpretiveFieldState(BaseModel):
    """Rich state for a single field with inference and values."""

    inference: Annotated[
        List[Inference],
        Field(default_factory=list, description="List of inference/reasoning steps"),
    ]
    values: Annotated[
        List[ValueConfidence],
        Field(
            default_factory=list,
            description="List of candidate values with confidence scores",
        ),
    ]


class InterpretiveStateSchema(RootModel[Dict[str, InterpretiveFieldState]]):
    """Interpretive state representation: rich format with inference and values.

    Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}

    Example:
        {
            "name": {
                "inference": [
                    {"content": "Extracted from input", "mutator_id": "extractor_1"}
                ],
                "values": [
                    {"value": "John Doe", "confidence": 0.95}
                ]
            }
        }
    """

    pass
