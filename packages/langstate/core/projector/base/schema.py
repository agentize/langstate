"""Pydantic schemas for base Projector module.

This module contains all data models used by the base Projector interface.
"""

from typing import Annotated, Dict, List

from pydantic import BaseModel, Field

from ...state.state.base import BaseState


def _default_conversation_history() -> List[Dict[str, str]]:
    return []


class ProjectionContext(BaseModel):
    """Base context provided to projectors for processing."""

    state: Annotated[
        BaseState,
        Field(description="Current state graph with field instances"),
    ]
    conversation_history: Annotated[
        List[Dict[str, str]],
        Field(description="Conversation history for context"),
    ] = Field(default_factory=_default_conversation_history)
    user_preferences: Annotated[
        Dict[str, object],
        Field(description="User preferences for projection"),
    ] = Field(default_factory=dict)
    strategy: Annotated[
        str,
        Field(description="Projection strategy hint"),
    ] = "highest_confidence"
    confidence_threshold: Annotated[
        float,
        Field(description="Default confidence threshold"),
    ] = 0.7
    metadata: Annotated[
        Dict[str, object],
        Field(description="Additional context metadata"),
    ] = Field(default_factory=dict)


class ProjectionResult(BaseModel):
    """Base result of a projection operation."""

    success: Annotated[
        bool,
        Field(description="Whether the projection was successful"),
    ] = True
    metadata: Annotated[
        Dict[str, object],
        Field(description="Additional metadata about the projection"),
    ] = Field(default_factory=dict)
