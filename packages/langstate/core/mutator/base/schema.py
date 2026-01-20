"""Pydantic schemas for Mutator module.

This module contains all data models used by the Mutator interface.
"""

from typing import Dict

from pydantic import BaseModel, Field, ConfigDict


class MutationResult(BaseModel):
    """Result of a mutation operation.

    Attributes:
        updated_state: The updated interpretive state graph after mutation
            Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}
        metadata: Additional metadata about the mutation
    """

    updated_state: Dict[str, object] = Field(default_factory=dict)
    metadata: Dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class MutationContext(BaseModel):
    """Context provided to the mutator for processing.

    Attributes:
        agent_input: The structured user input (AgentInput object)
        current_state: Current interpretive state graph with field instances
            Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}
        metadata: Additional context metadata
    """

    agent_input: Dict[str, object] = Field(default_factory=dict)
    current_state: Dict[str, object] = Field(default_factory=dict)
    metadata: Dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")
