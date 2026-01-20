"""Pydantic schemas for Interpretive State module.

This module contains all data models used by the Interpretive State.
Interpretive State uses rich format with inferences and value-confidence pairs.
"""

from typing import Dict, List

from pydantic import BaseModel, Field

from ..base.schema import Inference, ValueConfidence


class InterpretiveFieldState(BaseModel):
    """Rich state for a single field with inference and values.

    Attributes:
        inference: List of inference/reasoning steps
        values: List of candidate values with confidence scores
    """

    inference: List[Inference] = Field(default_factory=list)
    values: List[ValueConfidence] = Field(default_factory=list)


class InterpretiveState(BaseModel):
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

    __root__: Dict[str, InterpretiveFieldState]
