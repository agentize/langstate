"""Pydantic schemas for Interpretive State module.

This module contains all data models used by the Interpretive State.
Interpretive State uses rich format with inferences and value-confidence pairs.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from ..base.schema import Inference, ValueConfidence


class InterpretiveFieldState(BaseModel):
    """Interpretive state for a single field (rich format).

    Attributes:
        field_id: Unique identifier for the field
        inference: List of inference/reasoning steps
        values: List of candidate values with confidence scores
        metadata: Additional field metadata
    """

    field_id: str
    inference: List[Inference] = Field(default_factory=list)
    values: List[ValueConfidence] = Field(default_factory=list)
    metadata: Dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class InterpretiveStateData(BaseModel):
    """Data model for the entire interpretive state.

    Attributes:
        fields: Dictionary of field_id to InterpretiveFieldState
        metadata: Additional state metadata
    """

    fields: Dict[str, InterpretiveFieldState] = Field(default_factory=dict)
    metadata: Dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")
