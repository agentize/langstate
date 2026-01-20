"""Pydantic schemas for base Projector module.

This module contains all data models used by the base Projector interface.
"""

from typing import Dict, Optional

from pydantic import BaseModel, Field

from ...state.interpretive.schema import InterpretiveState
from ...state.canonical.schema import CanonicalState


class ProjectionContext(BaseModel):
    """Base context provided to projectors for processing.

    Attributes:
        interpretive_state: Current interpretive state graph with field instances
            Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}
        canonical_state: Current canonical state with resolved values (key: value)
        metadata: Additional context metadata
    """

    interpretive_state: InterpretiveState
    canonical_state: Optional[CanonicalState] = None
    metadata: Dict[str, object] = Field(default_factory=dict)


class ProjectionResult(BaseModel):
    """Base result of a projection operation.

    Attributes:
        success: Whether the projection was successful
        metadata: Additional metadata about the projection
    """

    success: bool = True
    metadata: Dict[str, object] = Field(default_factory=dict)
