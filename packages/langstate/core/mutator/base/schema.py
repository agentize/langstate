"""Pydantic schemas for Mutator module.

This module contains all data models used by the Mutator interface.
"""

from typing import Annotated, Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from ...state.state import State


class StructuredInput(BaseModel):
    """Structured user input model for Mutator."""

    prompt: Annotated[
        str,
        Field(
            description="The structured prompt input as a raw string.",
        ),
    ]

    message_id: Annotated[
        Optional[str],
        Field(
            description="Unique identifier for the message associated with this input."
        ),
    ] = None


class MutationContext(BaseModel):
    """Context provided to the mutator for processing."""

    input: Annotated[
        StructuredInput,
        Field(
            description="The structured user input.",
        ),
    ]
    state: Annotated[
        State,
        Field(
            description="Current interpretive state implementation instance."
            "Format: {key: {inference: {content, mutator_id, message_id} | null, values: [{value, confidence}]}}"
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
        State,
        Field(
            description="The updated interpretive state implementation instance after mutation."
            "Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}"
        ),
    ]
    metadata: Annotated[
        Dict[str, Any] | None,
        Field(description="Additional metadata about the mutation."),
    ] = None
