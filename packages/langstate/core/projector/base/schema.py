"""Pydantic schemas for base Projector module.

This module contains all data models used by the base Projector interface.
"""

from typing import Annotated, Dict, Optional

from pydantic import BaseModel, Field

from ...state.interpretive.schema import InterpretiveStateSchema
from ...state.canonical.schema import CanonicalStateSchema


class ProjectionContext(BaseModel):
    """Base context provided to projectors for processing."""

    interpretive_state: Annotated[
        InterpretiveStateSchema,
        Field(
            description="Current interpretive state graph with field instances. "
            "Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}"
        ),
    ]
    canonical_state: Annotated[
        Optional[CanonicalStateSchema],
        Field(
            default=None,
            description="Current canonical state with resolved values (key: value)",
        ),
    ]
    metadata: Annotated[
        Dict[str, object],
        Field(default_factory=dict, description="Additional context metadata"),
    ]


class ProjectionResult(BaseModel):
    """Base result of a projection operation."""

    success: Annotated[
        bool,
        Field(default=True, description="Whether the projection was successful"),
    ]
    metadata: Annotated[
        Dict[str, object],
        Field(
            default_factory=dict, description="Additional metadata about the projection"
        ),
    ]
