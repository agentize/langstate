"""Pydantic schemas for base State module.

This module contains all data models used by the State interface.
"""

from typing import Annotated

from pydantic import BaseModel, Field


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
