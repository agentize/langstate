"""Pydantic schemas for Mutator module.

This module contains all data models used by the Mutator interface.
"""

from typing import Annotated, Dict

from pydantic import BaseModel, Field

from ...state.interpretive.schema import InterpretiveState


class MutationResult(BaseModel):
    """Result of a mutation operation."""

    updated_state: Annotated[
        InterpretiveState,
        Field(
            description="The updated interpretive state graph after mutation. "
            "Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}"
        ),
    ]
    metadata: Annotated[
        Dict[str, object],
        Field(
            default_factory=dict, description="Additional metadata about the mutation"
        ),
    ]


class MutationContext(BaseModel):
    """Context provided to the mutator for processing."""

    agent_input: Annotated[
        Dict[str, object],
        Field(
            default_factory=dict,
            description="The structured user input (AgentInput object)",
        ),
    ]
    current_state: Annotated[
        InterpretiveState,
        Field(
            description="Current interpretive state graph with field instances. "
            "Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}"
        ),
    ]
    metadata: Annotated[
        Dict[str, object],
        Field(default_factory=dict, description="Additional context metadata"),
    ]
