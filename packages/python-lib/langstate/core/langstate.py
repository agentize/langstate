"""Main LangState class - the orchestrator for the system.

LangState is the main entry point for developers. It coordinates:
- Schema reading and initialization
- Creation of canonical state (key: value) and interpretive state
- User input processing via Mutator (updates interpretive state)
- Validation and projection via ProjectorCanonicalState (receives interpretive state,
  validates, can trigger actions, updates canonical state)
- UI/response generation via ProjectorUI

Interpretive State Format:
    {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}

This module follows agent SDK conventions (similar to OpenAI Agents SDK):
- LangState acts as an agent that can be invoked with structured input
- The main method is `invoke()` which processes agent input and returns responses
- Input is structured via `AgentInput` to support various interaction types
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from pathlib import Path

from pydantic import BaseModel, Field as PydField, ConfigDict

from ..models.field import State, FieldInstance, Schema
from .mutator import BaseMutator, MutationContext, MutationResult
from .projector import (
    BaseProjectorCanonicalState,
    CanonicalProjectionContext,
    CanonicalProjectionResult,
    BaseProjectorUI,
    UIProjectionContext,
    UIProjectionResult,
)


# =============================================================================
# Schema Reader Interface
# =============================================================================


class BaseSchemaReader(ABC):
    """Abstract base class for schema readers.

    Schema readers are responsible for loading and parsing schema definitions
    from various sources (YAML, JSON, OpenAPI specs, etc.).

    Example implementation:
        class OpenAPIYamlReader(BaseSchemaReader):
            def read(self, source: Union[str, Path, Dict[str, Any]]) -> Schema:
                from ..state.readers.yaml import load_schema_from_openapi_yaml
                return load_schema_from_openapi_yaml(source)
    """

    @abstractmethod
    def read(self, source: Union[str, Path, Dict[str, Any]]) -> Schema:
        """Read and parse schema from the given source.

        Args:
            source: Schema source - can be a file path (str/Path) or dict

        Returns:
            Parsed Schema object

        Raises:
            ValueError: If the schema source is invalid
            FileNotFoundError: If the source file doesn't exist
        """
        pass

    def validate(self, schema: Schema) -> bool:
        """Validate the parsed schema.

        Override this method to add custom validation logic.

        Args:
            schema: The schema to validate

        Returns:
            True if valid, raises exception otherwise
        """
        return True


# =============================================================================
# Agent Input Types
# =============================================================================


class InputType(str, Enum):
    """Type of input received from the user/client.

    Attributes:
        TEXT: Free-form text input (chat message, prompt response)
        ACTION: Button click, form submission, or other action trigger
        SELECTION: User selected from provided options
        CONFIRMATION: User confirmed or rejected a value
        FILE: File upload or attachment
        SYSTEM: System-generated input (timeout, error recovery, etc.)
    """

    TEXT = "text"
    ACTION = "action"
    SELECTION = "selection"
    CONFIRMATION = "confirmation"
    FILE = "file"
    SYSTEM = "system"


class AgentInput(BaseModel):
    """Structured input for agent invocation.

    This replaces simple string input to support various interaction types
    including button clicks, form submissions, file uploads, etc.

    Attributes:
        input_type: Type of input being provided
        text: Text content (for TEXT type or accompanying other types)
        action: Action identifier (for ACTION type, e.g., button_id, form_name)
        action_data: Additional data for the action (form fields, parameters)
        selection: Selected option(s) for SELECTION type
        field_id: Target field identifier (if input is for a specific field)
        confirmed: Confirmation status for CONFIRMATION type
        files: List of file references for FILE type
        metadata: Additional context or metadata

    Example usage:
        # Simple text input
        AgentInput(text="John Doe")

        # Button click
        AgentInput(
            input_type=InputType.ACTION,
            action="submit_form",
            action_data={"form_id": "registration"}
        )

        # Selection from options
        AgentInput(
            input_type=InputType.SELECTION,
            selection=["option_1", "option_2"],
            field_id="preferred_contact"
        )

        # Confirmation
        AgentInput(
            input_type=InputType.CONFIRMATION,
            field_id="email",
            confirmed=True
        )
    """

    input_type: InputType = InputType.TEXT
    text: Optional[str] = None
    action: Optional[str] = None
    action_data: Dict[str, Any] = PydField(default_factory=dict)
    selection: List[Any] = PydField(default_factory=list)
    field_id: Optional[str] = None
    confirmed: Optional[bool] = None
    files: List[Dict[str, Any]] = PydField(default_factory=list)
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")

    @classmethod
    def from_text(cls, text: str) -> "AgentInput":
        """Create AgentInput from simple text string.

        Args:
            text: The text input

        Returns:
            AgentInput instance with TEXT type
        """
        return cls(input_type=InputType.TEXT, text=text)

    @classmethod
    def from_action(
        cls, action: str, data: Optional[Dict[str, Any]] = None
    ) -> "AgentInput":
        """Create AgentInput from action trigger.

        Args:
            action: Action identifier
            data: Optional action data

        Returns:
            AgentInput instance with ACTION type
        """
        return cls(
            input_type=InputType.ACTION,
            action=action,
            action_data=data or {},
        )

    @classmethod
    def from_selection(
        cls, selection: List[Any], field_id: Optional[str] = None
    ) -> "AgentInput":
        """Create AgentInput from selection.

        Args:
            selection: Selected option(s)
            field_id: Optional target field

        Returns:
            AgentInput instance with SELECTION type
        """
        return cls(
            input_type=InputType.SELECTION,
            selection=selection,
            field_id=field_id,
        )

    @classmethod
    def from_confirmation(cls, field_id: str, confirmed: bool) -> "AgentInput":
        """Create AgentInput from confirmation.

        Args:
            field_id: Field being confirmed
            confirmed: Whether confirmed or rejected

        Returns:
            AgentInput instance with CONFIRMATION type
        """
        return cls(
            input_type=InputType.CONFIRMATION,
            field_id=field_id,
            confirmed=confirmed,
        )

    def is_empty(self) -> bool:
        """Check if the input is effectively empty (initial invocation).

        Returns:
            True if this represents an empty/initial input
        """
        return (
            self.text is None
            and self.action is None
            and not self.selection
            and self.confirmed is None
            and not self.files
        )


# =============================================================================
# Interaction Types
# =============================================================================


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
    """Abstract base class for the main LangState orchestrator (Agent).

    LangState is the main entry point for developers using this library.
    It acts as an agent that can be invoked with structured input, following
    conventions similar to OpenAI Agents SDK.

    It coordinates all components (Mutator, ProjectorCanonicalState, ProjectorUI)
    and manages the conversation flow.

    Interpretive State Format:
        {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}

    The flow is:
    1. Developer creates LangState instance with optional components
    2. Developer calls initialize() with config to setup schema and states
    3. Developer calls invoke() to get initial or next InteractionRequest
    4. Developer sends InteractionRequest to frontend (e.g., via HTTP)
    5. Developer receives user response and calls invoke() again
    6. Repeat until flow is complete (invoke returns ActionResult)

    Example usage:
        class MyLangState(LangState):
            async def initialize(self, config: LangStateConfig) -> None:
                # Load schema using the configured schema reader
                if self._schema_reader and config.schema_source:
                    self._schema = self._schema_reader.read(config.schema_source)
                
                from ..state.core.schema_to_init_state import (
                    schema_to_init_state,
                    canonical_to_interpretive_state
                )

                # Initialize components
                await self.mutator.initialize(self._schema)
                await self.projector_canonical.initialize(self._schema)
                await self.projector_ui.initialize(self._schema)

                # Create initial canonical state from schema (key: value)
                self._canonical_state = schema_to_init_state(self._schema)

                # Create interpretive state from canonical state
                # Format: {key: {inference: [], values: [{value, confidence}]}}
                self._state = canonical_to_interpretive_state(self._canonical_state)

            async def invoke(
                self, 
                agent_input: Optional[AgentInput] = None
            ) -> Union[InteractionRequest, ActionResult]:
                # If agent_input is empty (first call), generate initial interaction
                if agent_input is None or agent_input.is_empty():
                    return await self._create_interaction_request()

                # Run mutator to update interpretive state
                # Adds inference and value-confidence pairs
                mutation = await self.mutator.mutate(...)
                self._state = mutation.updated_state

                # Run canonical state projector to resolve values
                projection = await self.projector_canonical.project(...)
                self._canonical_state = projection.updated_state

                # Run UI projector to generate prompts/components
                ui_projection = await self.projector_ui.project(...)

                # Check if complete
                if self._is_state_complete(self._canonical_state):
                    return ActionResult(
                        state=self._state,
                        canonical_state=self._canonical_state
                    )

                # Generate next interaction
                return await self._create_interaction_request()

    Constructor Parameters:
        schema_reader: Optional BaseSchemaReader for loading schemas
        mutator: Optional BaseMutator for input processing (formerly Perceiver)
        projector_canonical: Optional BaseProjectorCanonicalState for validation (formerly Canonicalizer)
        projector_ui: Optional BaseProjectorUI for UI generation (formerly Interpreter)

    Customization:
        Developers can customize behavior by:
        - Providing components via constructor or setters
        - Configuring via LangStateConfig
        - Overriding methods in subclasses

        # Setup with constructor parameters
        langstate = MyLangState(
            schema_reader=OpenAPIYamlReader(),
            mutator=MyCustomMutator(),
            projector_canonical=MyLLMProjectorCanonical(),
            projector_ui=MyUIProjector()
        )
        
        # Or use setters
        langstate = MyLangState()
        langstate.set_schema_reader(OpenAPIYamlReader())
        langstate.set_mutator(MyCustomMutator())
        langstate.set_projector_canonical(MyLLMProjectorCanonical())
        langstate.set_projector_ui(MyUIProjector())
        
        # Initialize (loads schema, creates states)
        await langstate.initialize(LangStateConfig(schema_source="./schema.yaml"))
        
        # Get first interaction (invoke with no input)
        interaction = await langstate.invoke()
        
        # Process user text input
        result = await langstate.invoke(AgentInput.from_text("John Doe"))
        
        # Process button click
        result = await langstate.invoke(AgentInput.from_action("submit", {"form_id": "reg"}))
        
        # Process selection
        result = await langstate.invoke(AgentInput.from_selection(["option_1"]))
    """

    def __init__(
        self,
        schema_reader: Optional[BaseSchemaReader] = None,
        mutator: Optional[BaseMutator] = None,
        projector_canonical: Optional[BaseProjectorCanonicalState] = None,
        projector_ui: Optional[BaseProjectorUI] = None,
    ) -> None:
        """Initialize LangState with optional components.

        Args:
            schema_reader: Schema reader for loading schema definitions
            mutator: Mutator for processing user input (formerly Perceiver)
            projector_canonical: Canonical state projector for validation (formerly Canonicalizer)
            projector_ui: UI projector for generating prompts/components (formerly Interpreter)
        """
        self._schema_reader = schema_reader
        self._mutator = mutator
        self._projector_canonical = projector_canonical
        self._projector_ui = projector_ui
        self._schema: Optional[Schema] = None

    @abstractmethod
    async def initialize(self, config: LangStateConfig) -> None:
        """Initialize LangState with configuration.

        This method sets up schema, components, and creates both canonical
        and interpretive states. Does not return interaction - call invoke()
        to get the first InteractionRequest.

        Args:
            config: Configuration for this LangState instance
        """
        pass

    @abstractmethod
    async def invoke(
        self,
        agent_input: Optional[AgentInput] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Union[InteractionRequest, ActionResult]:
        """Invoke the agent with structured input and return next interaction or result.

        This is the main method developers call when they receive
        input from the frontend. Follows agent SDK conventions.

        Args:
            agent_input: Structured input from user (text, action, selection, etc.)
                        If None or empty, returns initial interaction.
            metadata: Optional additional metadata about the invocation

        Returns:
            InteractionRequest if more input needed, ActionResult if complete

        Example:
            # Initial invocation
            interaction = await langstate.invoke()

            # Text input
            result = await langstate.invoke(AgentInput.from_text("John"))

            # Button click
            result = await langstate.invoke(AgentInput.from_action("submit"))

            # Selection
            result = await langstate.invoke(AgentInput.from_selection(["opt1"]))
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
    def set_schema_reader(self, schema_reader: BaseSchemaReader) -> None:
        """Set a custom SchemaReader implementation.

        Args:
            schema_reader: Custom SchemaReader instance
        """
        pass

    @abstractmethod
    def set_schema(self, schema: Schema) -> None:
        """Set the schema directly.

        Args:
            schema: Schema instance to use
        """
        pass

    @abstractmethod
    def set_mutator(self, mutator: BaseMutator) -> None:
        """Set a custom Mutator implementation.

        Args:
            mutator: Custom Mutator instance
        """
        pass

    @abstractmethod
    def set_projector_canonical(self, projector: BaseProjectorCanonicalState) -> None:
        """Set a custom Canonical State Projector implementation.

        Args:
            projector: Custom ProjectorCanonicalState instance
        """
        pass

    @abstractmethod
    def set_projector_ui(self, projector: BaseProjectorUI) -> None:
        """Set a custom UI Projector implementation.

        Args:
            projector: Custom ProjectorUI instance
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

    # Property accessors for components
    @property
    def schema_reader(self) -> Optional[BaseSchemaReader]:
        """Get the current schema reader."""
        return self._schema_reader

    @property
    def mutator(self) -> Optional[BaseMutator]:
        """Get the current mutator."""
        return self._mutator

    @property
    def projector_canonical(self) -> Optional[BaseProjectorCanonicalState]:
        """Get the current canonical state projector."""
        return self._projector_canonical

    @property
    def projector_ui(self) -> Optional[BaseProjectorUI]:
        """Get the current UI projector."""
        return self._projector_ui

    @property
    def schema(self) -> Optional[Schema]:
        """Get the current schema."""
        return self._schema
