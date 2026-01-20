"""Pydantic schemas for Mutator module.

This module contains all data models used by the Mutator interface.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class MutationResult(BaseModel):
    """Result of a mutation operation.

    Attributes:
        updated_state: The updated interpretive state graph after mutation
            Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}
        extracted_fields: Fields that were extracted/updated in this mutation
        confidence_map: Mapping of field keys to their confidence scores
        raw_output: Optional raw output from the mutator (e.g., LLM response)
        metadata: Additional metadata about the mutation
    """

    updated_state: Dict[str, object] = Field(default_factory=dict)
    extracted_fields: Dict[str, object] = Field(default_factory=dict)
    confidence_map: Dict[str, float] = Field(default_factory=dict)
    raw_output: Optional[str] = None
    metadata: Dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class MutationContext(BaseModel):
    """Context provided to the mutator for processing.

    Attributes:
        agent_input: The structured user input (AgentInput object)
        current_state: Current interpretive state graph with field instances
            Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}
        schema: The schema definition
        conversation_history: Optional conversation history
        metadata: Additional context metadata
    """

    agent_input: Dict[str, object] = Field(default_factory=dict)
    current_state: Dict[str, object] = Field(default_factory=dict)
    schema: Optional[Dict[str, object]] = None
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    metadata: Dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")
