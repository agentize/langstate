"""Main LangState class - the orchestrator for the system.

LangState is the main entry point for developers. It coordinates:
- Schema reading and initialization
- User input processing via Perceiver
- State canonicalization via Canonicalizer
- UI/response generation via Interpreter
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from pathlib import Path

from pydantic import BaseModel, Field as PydField, ConfigDict

from ..models.field import State, FieldInstance, Schema
from .perceiver import BasePerceiver, PerceptionContext, PerceptionResult
from .canonicalizer import (
    BaseCanonicalizer,
    CanonicalizationContext,
    CanonicalizationResult,
)
from .interpreter import BaseInterpreter, InterpretationContext, InterpretationResult


class InteractionType(str, Enum):
    """Type of interaction required from the user.

    Attributes:
        PROMPT: Waiting for user text input
        SELECTION: Waiting for user to select from options
        CONFIRMATION: Waiting for user to confirm values
        ACTION: User triggered an action
        COMPLETE: Flow is complete, no more interaction needed
    """

    PROMPT = "prompt"
    SELECTION = "selection"
    CONFIRMATION = "confirmation"
    ACTION = "action"
    COMPLETE = "complete"


class InteractionRequest(BaseModel):
    """Request object returned when LangState needs user interaction.

    This is what developers receive when LangState needs input from the user.
    Developers can send this to their frontend via HTTP or other means.

    Attributes:
        interaction_type: Type of interaction needed
        prompt: Message/prompt for the user
        components: UI components to render
        options: Options for selection-type interactions
        state: Current interpretive state graph with field instances (includes value-confidence pairs)
        canonical_state: Canonical state with resolved values (business state, key:value only)
        pending_fields: Fields still needing values
        metadata: Additional metadata
    """

    interaction_type: InteractionType
    prompt: str = ""
    components: List[Any] = PydField(default_factory=list)
    options: Dict[str, List[Any]] = PydField(default_factory=dict)
    state: Optional[State] = None
    canonical_state: Optional[State] = None
    pending_fields: List[str] = PydField(default_factory=list)
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class ActionResult(BaseModel):
    """Result returned when the flow is complete and action can be taken.

    Attributes:
        state: Final interpretive state graph with all field snapshots (includes value-confidence pairs)
        canonical_state: Final canonical state with resolved values for action (business state, key:value only)
        success: Whether the flow completed successfully
        action_data: Data to be used for the action
        metadata: Additional metadata
    """

    state: State
    canonical_state: State
    success: bool = True
    action_data: Dict[str, Any] = PydField(default_factory=dict)
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class LangStateConfig(BaseModel):
    """Configuration for LangState instance.

    Attributes:
        schema_source: Path or dict for schema definition
        confidence_threshold: Minimum confidence for auto-canonicalization
        require_confirmation: Whether to require user confirmation for values
        conversation_history_limit: Max conversation history to maintain
        metadata: Additional configuration
    """

    schema_source: Optional[Union[str, Dict[str, Any]]] = None
    confidence_threshold: float = 0.7
    require_confirmation: bool = False
    conversation_history_limit: int = 100
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class LangState(ABC):
    """Abstract base class for the main LangState orchestrator.

    LangState is the main entry point for developers using this library.
    It coordinates all components (Perceiver, Canonicalizer, Interpreter)
    and manages the conversation flow.

    The flow is:
    1. Developer creates LangState instance with config
    2. LangState returns InteractionRequest when it needs user input
    3. Developer sends InteractionRequest to frontend (e.g., via HTTP)
    4. Developer receives user response and calls process_input()
    5. Repeat until flow is complete (returns ActionResult)

    Example usage:
        class MyLangState(LangState):
            async def initialize(self, config: LangStateConfig) -> InteractionRequest:
                # Load schema (using yaml reader and schema_to_init_state)
                from ..state.readers.yaml import load_schema_from_openapi_yaml
                from ..state.core.schema_to_init_state import schema_to_init_state

                schema = load_schema_from_openapi_yaml(config.schema_source)
                self._schema = schema

                # Initialize components
                await self.perceiver.initialize(self._schema)
                await self.canonicalizer.initialize(self._schema)
                await self.interpreter.initialize(self._schema)

                # Create initial state from schema
                self._state = schema_to_init_state(schema)

                # Return initial interaction request
                return await self._create_interaction_request()

            async def process_input(self, user_input: str) -> Union[InteractionRequest, ActionResult]:
                # Run perceiver to update field snapshots (updates interpretive state)
                perception = await self.perceiver.perceive(...)
                self._state = perception.updated_state  # Interpretive state with value-confidence pairs

                # Run canonicalizer to resolve values (creates canonical state)
                canonicalization = await self.canonicalizer.canonicalize(...)
                self._canonical_state = canonicalization.updated_state  # Canonical state with resolved values

                # Check if complete (all required fields have resolved values in canonical state)
                if self._is_state_complete(self._canonical_state):
                    return ActionResult(
                        state=self._state,  # Full interpretive state
                        canonical_state=self._canonical_state  # Resolved canonical state for action
                    )

                # Generate next interaction
                return await self._create_interaction_request()

    Customization:
        Developers can customize behavior by:
        - Providing custom Perceiver, Canonicalizer, Interpreter via setters
        - Configuring via LangStateConfig
        - Overriding methods in subclasses

        langstate = MyLangState()
        langstate.set_perceiver(MyCustomPerceiver())
        langstate.set_canonicalizer(MyLLMCanonicalizer())
    """

    @abstractmethod
    async def initialize(self, config: LangStateConfig) -> InteractionRequest:
        """Initialize LangState with configuration.

        This method sets up all components and returns the initial
        interaction request to start the conversation flow.

        Args:
            config: Configuration for this LangState instance

        Returns:
            Initial InteractionRequest to present to the user
        """
        pass

    @abstractmethod
    async def process_input(
        self, user_input: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Union[InteractionRequest, ActionResult]:
        """Process user input and return next interaction or result.

        This is the main method developers call when they receive
        input from the frontend.

        Args:
            user_input: The user's input (text response or action)
            metadata: Optional metadata about the input

        Returns:
            InteractionRequest if more input needed, ActionResult if complete
        """
        pass

    @abstractmethod
    async def get_current_state(self) -> State:
        """Get the current state graph.

        Returns:
            Current State with all field instances and their snapshots
        """
        pass

    @abstractmethod
    def set_perceiver(self, perceiver: BasePerceiver) -> None:
        """Set a custom Perceiver implementation.

        Args:
            perceiver: Custom Perceiver instance
        """
        pass

    @abstractmethod
    def set_canonicalizer(self, canonicalizer: BaseCanonicalizer) -> None:
        """Set a custom Canonicalizer implementation.

        Args:
            canonicalizer: Custom Canonicalizer instance
        """
        pass

    @abstractmethod
    def set_interpreter(self, interpreter: BaseInterpreter) -> None:
        """Set a custom Interpreter implementation.

        Args:
            interpreter: Custom Interpreter instance
        """
        pass

    @abstractmethod
    def add_action_handler(self, handler: Callable[[ActionResult], Any]) -> None:
        """Add a handler to be called when action is triggered.

        Args:
            handler: Callback function that receives ActionResult
        """
        pass

    @abstractmethod
    async def reset(self) -> InteractionRequest:
        """Reset the state and start over.

        Returns:
            Fresh InteractionRequest to start new conversation
        """
        pass

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history.

        Override this method to provide conversation history access.

        Returns:
            List of conversation entries
        """
        return []
