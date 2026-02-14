"""Pydantic schemas for LLM Mutator module.

This module contains data models specific to LLM-based mutation operations.
"""

from typing import Annotated, Any, Dict, Optional

from pydantic import BaseModel, Field

from ...state.interpretive.state import InterpretiveState


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
        InterpretiveState,
        Field(
            description="Current interpretive state implementation instance."
            "Format: {key: {inference: {content, mutator_id, message_id} | null, values: [{value, confidence}]}}"
        ),
    ]
    metadata: Annotated[
        Dict[str, Any] | None,
        Field(description="Additional metadata about the mutation."),
    ] = None
