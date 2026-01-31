"""Pydantic schemas for Interpretive State module.

This module contains all data models used by the Interpretive State.
Interpretive State uses rich format with inferences and value-confidence pairs.
"""

from typing import Annotated, Dict, List

from pydantic import BaseModel, Field, RootModel


class Inference(BaseModel):
    """Inference step that led to a value."""

    content: Annotated[str, Field(description="Description of the inference/reasoning")]
    mutator_id: Annotated[
        str,
        Field(description="Identifier of the mutator that generated this inference"),
    ] = "unknown"


class ValueConfidence(BaseModel):
    """Value with associated confidence score."""

    value: Annotated[object, Field(description="The actual value")]
    confidence: Annotated[float, Field(description="Confidence score (0.0 to 1.0)")] = (
        0.0
    )


class InterpretiveFieldState(BaseModel):
    """Rich state for a single field with inference and values."""

    inference: Annotated[
        List[Inference],
        Field(description="List of inference/reasoning steps"),
    ] = []
    values: Annotated[
        List[ValueConfidence],
        Field(description="List of candidate values with confidence scores"),
    ] = []


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
