"""Pydantic schemas for Mutator module.

This module contains all data models used by the Mutator interface.
"""

from typing import Annotated, Any, Dict

from pydantic import BaseModel, ConfigDict, Field

from ...state.state import State


class MutationContext(BaseModel):
    """Context provided to the mutator for processing."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    input: Annotated[
        Dict[str, object],
        Field(
            default_factory=dict,
            description="The structured user input",
        ),
    ]
    state: Annotated[
        State,
        Field(description="Current state implementation instance"),
    ]
    metadata: Annotated[
        Dict[str, Any] | None,
        Field(description="Additional metadata about the mutation"),
    ] = None


class MutationResult(BaseModel):
    """Result of a mutation operation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    state: Annotated[
        State,
        Field(description="The updated state implementation instance after mutation"),
    ]
    metadata: Annotated[
        Dict[str, Any] | None,
        Field(description="Additional metadata about the mutation"),
    ] = None
