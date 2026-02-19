"""Pydantic schemas for base Projector module.

This module contains all data models used by the base Projector interface.
"""

from typing import Annotated, Dict, List

from pydantic import BaseModel, Field

from ...state.state.schema import StateSchema


class ProjectionContext(BaseModel):
    """Base context provided to projectors for processing."""

    state: Annotated[
        StateSchema,
        Field(description="Current state graph with field instances"),
    ]
    conversation_history: Annotated[
        List[Dict[str, str]],
        Field(default_factory=list, description="Conversation history for context"),
    ]
    user_preferences: Annotated[
        Dict[str, object],
        Field(default_factory=dict, description="User preferences for projection"),
    ]
    strategy: Annotated[
        str,
        Field(default="highest_confidence", description="Projection strategy hint"),
    ]
    confidence_threshold: Annotated[
        float,
        Field(default=0.7, description="Default confidence threshold"),
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
