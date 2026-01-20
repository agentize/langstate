"""Pydantic schemas for Mutator module.

This module contains all data models used by the Mutator interface.
"""

from typing import Dict

from pydantic import BaseModel, Field

from ...state.interpretive.schema import InterpretiveState


class MutationResult(BaseModel):
    """Result of a mutation operation.

    Attributes:
        updated_state: The updated interpretive state graph after mutation
            Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}
        metadata: Additional metadata about the mutation
    """

    updated_state: InterpretiveState
    metadata: Dict[str, object] = Field(default_factory=dict)


class MutationContext(BaseModel):
    """Context provided to the mutator for processing.

    Attributes:
        agent_input: The structured user input (AgentInput object)
        current_state: Current interpretive state graph with field instances
            Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}
        metadata: Additional context metadata
    """

    agent_input: Dict[str, object] = Field(default_factory=dict)
    current_state: InterpretiveState
    metadata: Dict[str, object] = Field(default_factory=dict)
