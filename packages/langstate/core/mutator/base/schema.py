"""Pydantic schemas for Mutator module.

This module contains all data models used by the Mutator interface.
"""

from typing import Annotated, Any, Dict

from pydantic import BaseModel, ConfigDict, Field

from ...state.interpretive.state import InterpretiveState


class StructuredInput(BaseModel):
    """Structured user input model for Mutator."""

    prompt: Annotated[
        str,
        Field(
            description="The structured prompt input as a raw string.",
        ),
    ]


class MutationContext(BaseModel):
    """Context provided to the mutator for processing."""

    input: Annotated[
        StructuredInput,
        Field(
            description="The structured user input.",
        ),
    ]
    state: Annotated[
        InterpretiveState,
        Field(
            description="Current interpretive state implementation instance."
            "Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}"
        ),
    ]
    metadata: Annotated[
        Dict[str, Any] | None,
        Field(description="Additional metadata about the mutation."),
    ] = None


class MutationResult(BaseModel):
    """Result of a mutation operation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    updated_state: Annotated[
        InterpretiveState,
        Field(
            description="The updated interpretive state implementation instance after mutation."
            "Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}"
        ),
    ]
    metadata: Annotated[
        Dict[str, Any] | None,
        Field(description="Additional metadata about the mutation."),
    ] = None
