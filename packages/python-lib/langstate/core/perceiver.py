"""Perceiver interface for LangState.

The Perceiver is responsible for:
- Receiving user input (prompts, actions from frontend)
- Interpreting the input in the context of the current interpretive state
- Updating interpretive state by adding value-confidence pairs to field snapshots
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field as PydField, ConfigDict

if TYPE_CHECKING:
    from ..models.field import State, Schema


class PerceptionResult(BaseModel):
    """Result of a perception operation.

    Attributes:
        updated_state: The updated interpretive state graph after perception (key: [{value, confidence}])
        extracted_fields: Fields that were extracted/updated in this perception
        confidence_map: Mapping of field keys to their confidence scores
        raw_output: Optional raw output from the perceiver (e.g., LLM response)
        metadata: Additional metadata about the perception
    """

    updated_state: Any  # State - interpretive state with value-confidence pairs
    extracted_fields: Dict[str, Any] = PydField(default_factory=dict)
    confidence_map: Dict[str, float] = PydField(default_factory=dict)
    raw_output: Optional[str] = None
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class PerceptionContext(BaseModel):
    """Context provided to the perceiver for processing.

    Attributes:
        user_input: The raw user input (text prompt or action)
        current_state: Current interpretive state graph with field instances (key: [{value, confidence}])
        schema: The schema definition
        conversation_history: Optional conversation history
        metadata: Additional context metadata
    """

    user_input: str
    current_state: Any  # State - interpretive state
    schema: Optional[Any] = None  # Schema
    conversation_history: list = PydField(default_factory=list)
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class BasePerceiver(ABC):
    """Abstract base class for Perceiver implementations.

    The Perceiver processes user input and updates the interpretive state graph
    by adding value-confidence pairs to field snapshots. It is responsible for 
    extracting values from natural language input and assigning confidence scores.

    Implementations might include:
    - LLM-based perceiver (uses language models to extract values)
    - Rule-based perceiver (uses pattern matching and rules)
    - Hybrid perceiver (combines multiple approaches)

    Example usage:
        class MyPerceiver(BasePerceiver):
            async def perceive(self, context: PerceptionContext) -> PerceptionResult:
                # Extract values from user input using LLM
                extracted = await self.llm.extract(context.user_input)

                # Update interpretive state by adding value-confidence pairs
                new_state = context.current_state.copy()
                for field_id, value in extracted.items():
                    # Add new value-confidence pair to field instance
                    field_instance = new_state.nodes[field_id].value
                    field_instance.add_snapshot(
                        value_confidence_list=[
                            ValueConfidence(value=value, score=0.8)
                        ],
                        status=FieldStatusEnum.UPDATED,
                        updater=self.updater_info
                    )

                return PerceptionResult(
                    updated_state=new_state,  # Updated interpretive state
                    extracted_fields=extracted,
                    confidence_map={k: 0.8 for k in extracted.keys()}
                )
    """

    @abstractmethod
    async def perceive(self, context: PerceptionContext) -> PerceptionResult:
        """Process user input and update the interpretive state graph.

        This method takes the user's input along with the current interpretive state
        and returns an updated interpretive state with value-confidence pairs extracted 
        from the input added to field snapshots.

        Args:
            context: PerceptionContext containing user input and current state

        Returns:
            PerceptionResult with the updated state graph
        """
        pass

    @abstractmethod
    async def initialize(self, schema: Any) -> None:
        """Initialize the perceiver with a schema.

        This method is called when the perceiver is first set up,
        allowing it to configure itself based on the schema definition.

        Args:
            schema: The schema definition to use for perception
        """
        pass

    def validate_input(self, user_input: str) -> bool:
        """Validate user input before processing.

        Override this method to add custom input validation.

        Args:
            user_input: The raw user input

        Returns:
            True if input is valid, False otherwise
        """
        return bool(user_input and user_input.strip())
