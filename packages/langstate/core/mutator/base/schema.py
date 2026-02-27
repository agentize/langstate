"""Pydantic schemas for Mutator module.

This module contains all data models used by the Mutator interface.
"""

from typing import Annotated, Any, Dict

from pydantic import BaseModel, Field

from ...state.state.state import State


class MutationResult(BaseModel):
    """Result of a mutation operation."""

    updated_state: Annotated[
        State,
        Field(
            description="The updated state implementation instance after mutation."
            "Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}"
        ),
    ]
    metadata: Annotated[
        Dict[str, Any] | None,
        Field(description="Additional metadata about the mutation."),
    ] = None
