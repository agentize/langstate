"""Pydantic schemas for State module.

This module contains all data models used by the State.
State uses rich format with inferences and value-confidence pairs.
"""

from typing import Annotated, Dict, List, Optional

from pydantic import BaseModel, Field, RootModel


class Inference(BaseModel):
    """Inference step that led to a value."""

    content: Annotated[str, Field(description="Description of the inference/reasoning")]
    mutator_id: Annotated[
        Optional[str],
        Field(description="Identifier of the mutator that generated this inference"),
    ] = None
    message_id: Annotated[
        Optional[str],
        Field(description="Message ID associated with this inference"),
    ] = None


class ValueConfidence(BaseModel):
    """Value with associated confidence score."""

    value: Annotated[object, Field(description="The actual value")]
    confidence: Annotated[
        float,
        Field(
            ge=-1.0,
            le=1.0,
            description="Confidence score from -1.0 to 1.0",
        ),
    ] = 0.0


class InterpretiveField(BaseModel):
    """Rich state for a single field with inference and values."""

    inference: Annotated[
        Optional[Inference],
        Field(description="Latest inference/reasoning step"),
    ] = None
    values: Annotated[
        List[ValueConfidence],
        Field(description="List of candidate values with confidence scores"),
    ] = []


class StateSchema(RootModel[Dict[str, InterpretiveField]]):
    """State representation: rich format with inference and values.

    Format: {key: {inference: {content, mutator_id, message_id} | null, values: [{value, confidence}]}}

    Example:
        {
            "name": {
                "inference": {
                    "content": "Extracted from input",
                    "mutator_id": "extractor_1",
                    "message_id": "msg_123"
                },
                "values": [
                    {"value": "John Doe", "confidence": 0.95}
                ]
            }
        }
    """

    pass
