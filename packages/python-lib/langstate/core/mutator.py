"""Mutator interface for LangState.

The Mutator is responsible for:
- Receiving user input (prompts, actions from frontend)
- Interpreting the input in the context of the current interpretive state
- Updating interpretive state by adding inferences and value-confidence pairs to field snapshots

Note: Formerly known as "Perceiver", renamed to "Mutator" to better reflect its role
in mutating/updating the interpretive state based on user input.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field as PydField, ConfigDict

if TYPE_CHECKING:
    from ..models.field import State, Schema


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

    updated_state: Any  # State - interpretive state with inference and value-confidence pairs
    extracted_fields: Dict[str, Any] = PydField(default_factory=dict)
    confidence_map: Dict[str, float] = PydField(default_factory=dict)
    raw_output: Optional[str] = None
    metadata: Dict[str, Any] = PydField(default_factory=dict)

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

    agent_input: Any  # AgentInput - structured input from user
    current_state: Any  # State - interpretive state
    schema: Optional[Any] = None  # Schema
    conversation_history: list = PydField(default_factory=list)
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class BaseMutator(ABC):
    """Abstract base class for Mutator implementations.

    The Mutator processes user input and updates the interpretive state graph
    by adding inferences and value-confidence pairs to field snapshots. It is 
    responsible for extracting values from natural language input and assigning 
    confidence scores.

    The interpretive state format is:
        {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}

    Where:
        - inference: List of reasoning/inference steps that led to the values
        - values: List of candidate values with their confidence scores

    Implementations might include:
    - LLM-based mutator (uses language models to extract values)
    - Rule-based mutator (uses pattern matching and rules)
    - Hybrid mutator (combines multiple approaches)

    Example usage:
        class MyMutator(BaseMutator):
            async def mutate(self, context: MutationContext) -> MutationResult:
                # Extract values from user input using LLM
                extracted = await self.llm.extract(context.agent_input)

                # Update interpretive state by adding inference and value-confidence pairs
                new_state = context.current_state.copy()
                for field_id, value in extracted.items():
                    field_instance = new_state.nodes[field_id].value
                    # Add inference about how value was derived
                    inference = Inference(
                        content=f"Extracted '{value}' from user input",
                        mutator_id=self.mutator_id
                    )
                    # Add new value-confidence pair
                    field_instance.add_snapshot(
                        inference_list=[inference],
                        value_confidence_list=[
                            ValueConfidence(value=value, confidence=0.8)
                        ],
                        status=FieldStatusEnum.UPDATED,
                        updater=self.updater_info
                    )

                return MutationResult(
                    updated_state=new_state,
                    extracted_fields=extracted,
                    confidence_map={k: 0.8 for k in extracted.keys()}
                )
    """

    # Unique identifier for this mutator instance
    mutator_id: str = "base_mutator"

    @abstractmethod
    async def mutate(self, context: MutationContext) -> MutationResult:
        """Process user input and update the interpretive state graph.

        This method takes the user's input along with the current interpretive state
        and returns an updated interpretive state with inferences and value-confidence 
        pairs extracted from the input added to field snapshots.

        Args:
            context: MutationContext containing agent input and current state

        Returns:
            MutationResult with the updated state graph
        """
        pass

    @abstractmethod
    async def initialize(self, schema: Any) -> None:
        """Initialize the mutator with a schema.

        This method is called when the mutator is first set up,
        allowing it to configure itself based on the schema definition.

        Args:
            schema: The schema definition to use for mutation
        """
        pass

    def validate_input(self, agent_input: Any) -> bool:
        """Validate agent input before processing.

        Override this method to add custom input validation.

        Args:
            agent_input: The AgentInput to validate

        Returns:
            True if input is valid, False otherwise
        """
        if agent_input is None:
            return False
        # Check if it has any meaningful content
        return not getattr(agent_input, 'is_empty', lambda: True)()


# Backward compatibility aliases (deprecated)
BasePerceiver = BaseMutator
PerceptionResult = MutationResult
PerceptionContext = MutationContext
