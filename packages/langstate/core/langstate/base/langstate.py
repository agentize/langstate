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

from abc import ABC, abstractmethod
from typing import Callable, Dict, Generic, List, Optional, Union

from ...mutator.base.base import TContext

from ...spec_extractor import BaseSpecExtractor, Schema
from ...mutator import BaseMutator
from ...projector import (
    BaseProjectorCanonicalState,
    BaseProjectorUI,
)
from ...state import BaseCanonicalState, BaseInterpretiveState

from .schema import (
    AgentInput,
    InteractionRequest,
    ActionResultData,
    LangStateConfig,
)

class LangState(ABC, Generic[TContext]):
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
    6. Repeat until flow is complete (invoke returns ActionResultData)

    Example usage:
        class MyLangState(LangState):
            async def initialize(self, config: LangStateConfig) -> None:
                # Load schema using the configured spec extractor
                if self._spec_extractor and config.schema_source:
                    self._schema = self._spec_extractor.read(config.schema_source)

                # Initialize components
                if self._mutator:
                    await self._mutator.initialize(self._schema)
                if self._projector_canonical:
                    await self._projector_canonical.initialize(self._schema)

                # Initialize all UI projectors
                for projector in self._projectors_ui:
                    await projector.initialize(self._schema)

                # Create initial canonical state from schema (key: value)
                self._canonical_state = CanonicalState()

                # Create interpretive state from canonical state
                # Format: {key: {inference: [], values: [{value, confidence}]}}
                self._interpretive_state = InterpretiveState()

            async def invoke(
                self,
                agent_input: Optional[AgentInput] = None
            ) -> Union[InteractionRequest, ActionResultData]:
                # If agent_input is empty (first call), generate initial interaction
                if agent_input is None or agent_input.is_empty():
                    return await self._create_interaction_request()

                # Run mutator to update interpretive state
                # Adds inference and value-confidence pairs
                mutation = await self.mutator.mutate(...)
                self._interpretive_state = mutation.updated_state

                # Run canonical state projector to resolve values
                projection = await self.projector_canonical.project(...)
                self._canonical_state = projection.updated_state

                # Run all UI projectors to generate prompts/components
                ui_projections = []
                for projector in self._projectors_ui:
                    ui_projection = await projector.project(...)
                    ui_projections.append(ui_projection)

                # Check if complete
                if self._is_state_complete(self._canonical_state):
                    return ActionResultData(
                        state=self._interpretive_state.to_dict(),
                        canonical_state=self._canonical_state.to_dict()
                    )

                # Generate next interaction
                return await self._create_interaction_request()

    Constructor Parameters:
        spec_extractor: Optional BaseSpecExtractor for loading schemas
        mutator: Optional BaseMutator for input processing
        projector_canonical: Optional BaseProjectorCanonicalState for validation
        projectors_ui: Optional BaseProjectorUI or List[BaseProjectorUI] for UI generation

    Customization:
        Developers can customize behavior by:
        - Providing components via constructor or setters
        - Configuring via LangStateConfig
        - Overriding methods in subclasses

        # Setup with constructor parameters (single projector)
        langstate = MyLangState(
            spec_extractor=OpenAPIYamlExtractor(),
            mutator=MyCustomMutator(),
            projector_canonical=MyLLMProjectorCanonical(),
            projectors_ui=MyUIProjector()
        )

        # Setup with multiple projectors
        langstate = MyLangState(
            spec_extractor=OpenAPIYamlExtractor(),
            mutator=MyCustomMutator(),
            projector_canonical=MyLLMProjectorCanonical(),
            projectors_ui=[MyUIProjector(), MyUIInterpreterA()]
        )

        # Or use setters
        langstate = MyLangState()
        langstate.set_spec_extractor(OpenAPIYamlExtractor())
        langstate.set_mutator(MyCustomMutator())
        langstate.set_projector_canonical(MyLLMProjectorCanonical())
        langstate.set_projector_ui(MyUIProjector())

        # Or add projectors one by one
        langstate.add_projector_ui(MyUIInterpreterA())
        langstate.add_projector_ui(MyUIInterpreterB())

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
        spec_extractor: Optional[BaseSpecExtractor] = None,
        mutator: Optional[BaseMutator[TContext]] = None,
        projector_canonical: Optional[BaseProjectorCanonicalState] = None,
        projectors_ui: Optional[Union[BaseProjectorUI, List[BaseProjectorUI]]] = None,
    ) -> None:
        """Initialize LangState with optional components.

        Args:
            spec_extractor: Spec extractor for loading schema definitions
            mutator: Mutator for processing user input
            projector_canonical: Canonical state projector for validation
            projectors_ui: UI projector(s) for generating prompts/components.
                          Can be a single projector or a list of projectors.
        """
        self._spec_extractor = spec_extractor
        self._mutator = mutator
        self._projector_canonical = projector_canonical

        # Convert single projector to list
        if projectors_ui is None:
            self._projectors_ui: List[BaseProjectorUI] = []
        elif isinstance(projectors_ui, list):
            self._projectors_ui = projectors_ui
        else:
            self._projectors_ui = [projectors_ui]

        self._schema: Optional[Schema] = None
        self._canonical_state: Optional[BaseCanonicalState] = None
        self._interpretive_state: Optional[BaseInterpretiveState] = None
        self._conversation_history: List[Dict[str, str]] = []
        self._action_handlers: List[Callable[[ActionResultData], object]] = []

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
        metadata: Optional[Dict[str, object]] = None,
    ) -> Union[InteractionRequest, ActionResultData]:
        """Invoke the agent with structured input and return next interaction or result.

        This is the main method developers call when they receive
        input from the frontend. Follows agent SDK conventions.

        Args:
            agent_input: Structured input from user (text, action, selection, etc.)
                        If None or empty, returns initial interaction.
            metadata: Optional additional metadata about the invocation

        Returns:
            InteractionRequest if more input needed, ActionResultData if complete

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
    async def get_current_state(self) -> BaseInterpretiveState:
        """Get the current interpretive state.

        Returns:
            Current InterpretiveState with all field instances and their snapshots
        """
        pass

    @abstractmethod
    async def get_canonical_state(self) -> BaseCanonicalState:
        """Get the current canonical state.

        Returns:
            Current CanonicalState with resolved values
        """
        pass

    def set_spec_extractor(self, spec_extractor: BaseSpecExtractor) -> None:
        """Set a custom SpecExtractor implementation.

        Args:
            spec_extractor: Custom SpecExtractor instance
        """
        self._spec_extractor = spec_extractor

    def set_schema(self, schema: Schema) -> None:
        """Set the schema directly.

        Args:
            schema: Schema instance to use
        """
        self._schema = schema

    def set_mutator(self, mutator: BaseMutator[TContext]) -> None:
        """Set a custom Mutator implementation.

        Args:
            mutator: Custom Mutator instance
        """
        self._mutator = mutator

    def set_projector_canonical(self, projector: BaseProjectorCanonicalState) -> None:
        """Set a custom Canonical State Projector implementation.

        Args:
            projector: Custom ProjectorCanonicalState instance
        """
        self._projector_canonical = projector

    def set_projector_ui(
        self, projector: Union[BaseProjectorUI, List[BaseProjectorUI]]
    ) -> None:
        """Set UI Projector implementation(s), replacing existing projectors.

        Args:
            projector: Custom ProjectorUI instance or list of instances
        """
        if isinstance(projector, list):
            self._projectors_ui = projector
        else:
            self._projectors_ui = [projector]

    def add_projector_ui(self, projector: BaseProjectorUI) -> None:
        """Add a UI Projector to the list of projectors.

        Args:
            projector: Custom ProjectorUI instance to add
        """
        self._projectors_ui.append(projector)

    def add_action_handler(self, handler: Callable[[ActionResultData], object]) -> None:
        """Add a handler to be called when action is triggered.

        Args:
            handler: Callback function that receives ActionResultData
        """
        self._action_handlers.append(handler)

    @abstractmethod
    async def reset(self) -> InteractionRequest:
        """Reset the state and start over.

        Returns:
            Fresh InteractionRequest to start new conversation
        """
        pass

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history.

        Returns:
            List of conversation entries
        """
        return self._conversation_history

    # Property accessors for components
    @property
    def spec_extractor(self) -> Optional[BaseSpecExtractor]:
        """Get the current spec extractor."""
        return self._spec_extractor

    @property
    def mutator(self) -> Optional[BaseMutator[TContext]]:
        """Get the current mutator."""
        return self._mutator

    @property
    def projector_canonical(self) -> Optional[BaseProjectorCanonicalState]:
        """Get the current canonical state projector."""
        return self._projector_canonical

    @property
    def projectors_ui(self) -> List[BaseProjectorUI]:
        """Get the list of current UI projectors."""
        return self._projectors_ui

    @property
    def schema(self) -> Optional[Schema]:
        """Get the current schema."""
        return self._schema
