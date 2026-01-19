"""Projector interface for LangState.

The Projector is responsible for:
- Projecting internal state to external representations
- Base interface for both UI projection and Canonical State projection

This module defines the base Projector interface and two specialized implementations:
- ProjectorUI: Projects interpretive state to UI components and prompts
- ProjectorCanonicalState: Projects interpretive state to canonical business state

Note: Formerly known as "Interpreter" (for UI) and "Canonicalizer" (for canonical state),
renamed to "Projector" to unify the concept of projecting internal state to different
output formats.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field as PydField, ConfigDict

if TYPE_CHECKING:
    from ..models.field import State, Schema


# =============================================================================
# Base Projector Interface
# =============================================================================


class ProjectionContext(BaseModel):
    """Base context provided to projectors for processing.

    Attributes:
        interpretive_state: Current interpretive state graph with field instances
            Format: {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}
        canonical_state: Current canonical state with resolved values (key: value)
        schema: The schema definition
        metadata: Additional context metadata
    """

    interpretive_state: Any  # State - interpretive state
    canonical_state: Optional[Any] = None  # State - canonical state
    schema: Optional[Any] = None  # Schema
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class ProjectionResult(BaseModel):
    """Base result of a projection operation.

    Attributes:
        success: Whether the projection was successful
        metadata: Additional metadata about the projection
    """

    success: bool = True
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class BaseProjector(ABC):
    """Abstract base class for all Projector implementations.

    A Projector transforms internal state into a specific output format.
    This is the base interface that specialized projectors inherit from.

    Specialized implementations:
    - ProjectorUI: Transforms state into UI components and user prompts
    - ProjectorCanonicalState: Transforms interpretive state into canonical business state
    """

    @abstractmethod
    async def project(self, context: ProjectionContext) -> ProjectionResult:
        """Project the state to the target format.

        Args:
            context: ProjectionContext containing current state

        Returns:
            ProjectionResult with the projection output
        """
        pass

    @abstractmethod
    async def initialize(self, schema: Any) -> None:
        """Initialize the projector with a schema.

        This method is called when the projector is first set up,
        allowing it to configure itself based on the schema definition.

        Args:
            schema: The schema definition to use for projection
        """
        pass


# =============================================================================
# UI Projector (formerly Interpreter)
# =============================================================================


class UIComponentType(str, Enum):
    """Types of UI components that can be generated.

    Attributes:
        TEXT_INPUT: Simple text input field
        SELECT: Dropdown/select component
        MULTI_SELECT: Multiple selection component
        DATE_PICKER: Date selection component
        NUMBER_INPUT: Numeric input field
        RADIO: Radio button group
        CHECKBOX: Checkbox or checkbox group
        SLIDER: Slider/range component
        FILE_UPLOAD: File upload component
        TABLE: Table/grid display
        MAP_VIEW: Map visualization
        CUSTOM: Custom component type
    """

    TEXT_INPUT = "text_input"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    DATE_PICKER = "date_picker"
    NUMBER_INPUT = "number_input"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    SLIDER = "slider"
    FILE_UPLOAD = "file_upload"
    TABLE = "table"
    MAP_VIEW = "map_view"
    CUSTOM = "custom"


class UIComponent(BaseModel):
    """Representation of a UI component.

    Attributes:
        field_key: The field this component is for
        component_type: Type of UI component
        label: Display label for the component
        placeholder: Placeholder text
        options: Options for select-type components
        validation: Client-side validation rules
        default_value: Default value for the component
        disabled: Whether the component is disabled
        required: Whether the field is required
        metadata: Additional component metadata
    """

    field_key: str
    component_type: UIComponentType
    label: str = ""
    placeholder: str = ""
    options: List[Dict[str, Any]] = PydField(default_factory=list)
    validation: Dict[str, Any] = PydField(default_factory=dict)
    default_value: Optional[Any] = None
    disabled: bool = False
    required: bool = False
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class UIProjectionContext(ProjectionContext):
    """Context provided to the UI projector for processing.

    Extends ProjectionContext with UI-specific fields.

    Attributes:
        conversation_history: Conversation history for context
        user_preferences: User preferences for UI generation
    """

    conversation_history: List[Dict[str, str]] = PydField(default_factory=list)
    user_preferences: Dict[str, Any] = PydField(default_factory=dict)


class UIProjectionResult(ProjectionResult):
    """Result of a UI projection operation.

    Attributes:
        prompt: The generated prompt/message for the user
        components: List of UI components to display
        suggestions: Suggested values/actions for the user
        is_complete: Whether the form/flow is complete
        next_fields: Fields to focus on next
    """

    prompt: str = ""
    components: List[UIComponent] = PydField(default_factory=list)
    suggestions: Dict[str, List[Any]] = PydField(default_factory=dict)
    is_complete: bool = False
    next_fields: List[str] = PydField(default_factory=list)


class BaseProjectorUI(BaseProjector):
    """Abstract base class for UI Projector implementations.

    The UI Projector generates UI components and LLM completions based on
    the current state graph. It bridges the gap between the internal state
    representation and what the user sees.

    Responsibilities:
    - Map field schemas to appropriate UI component types
    - Generate natural language prompts/responses
    - Suggest values based on context
    - Determine which fields to focus on next

    Example usage:
        class ChatProjectorUI(BaseProjectorUI):
            async def project(
                self,
                context: UIProjectionContext
            ) -> UIProjectionResult:
                # Generate components for unfilled fields
                components = []
                for node_id, node in context.interpretive_state.nodes.items():
                    field_instance = node.value
                    if not self._has_resolved_value(field_instance):
                        component = self.map_field_to_component(field_instance)
                        components.append(component)

                # Generate prompt
                prompt = await self.generate_prompt(context)

                return UIProjectionResult(
                    prompt=prompt,
                    components=components,
                    is_complete=self._is_complete(context)
                )
    """

    @abstractmethod
    async def project(self, context: UIProjectionContext) -> UIProjectionResult:
        """Generate UI components and prompt based on current state.

        This method takes the current state and generates the appropriate
        UI representation and natural language prompt for the user.

        Args:
            context: UIProjectionContext containing current state

        Returns:
            UIProjectionResult with UI components and prompt
        """
        pass

    @abstractmethod
    async def generate_prompt(self, context: UIProjectionContext) -> str:
        """Generate a natural language prompt for the user.

        Args:
            context: UIProjectionContext containing current state

        Returns:
            Generated prompt string
        """
        pass

    @abstractmethod
    def map_field_to_component(
        self, field_key: str, schema: Optional[Any] = None
    ) -> UIComponent:
        """Map a field to an appropriate UI component.

        Args:
            field_key: The field key to map
            schema: Optional schema for field metadata

        Returns:
            UIComponent appropriate for the field
        """
        pass

    def get_supported_components(self) -> List[UIComponentType]:
        """Get list of supported UI component types.

        Override this method to specify which component types
        this projector supports.

        Returns:
            List of supported UIComponentType values
        """
        return list(UIComponentType)


# =============================================================================
# Canonical State Projector (formerly Canonicalizer)
# =============================================================================


class CanonicalProjectionStrategy(str, Enum):
    """Strategy for resolving multiple candidate values to canonical state.

    Attributes:
        HIGHEST_CONFIDENCE: Select value with highest confidence score
        THRESHOLD: Select value only if confidence exceeds threshold
        LLM_RESOLVE: Use LLM to resolve ambiguous values
        MANUAL: Require manual user confirmation
        CUSTOM: Use custom resolution logic
    """

    HIGHEST_CONFIDENCE = "highest_confidence"
    THRESHOLD = "threshold"
    LLM_RESOLVE = "llm_resolve"
    MANUAL = "manual"
    CUSTOM = "custom"


class CanonicalProjectionContext(ProjectionContext):
    """Context provided to the canonical state projector for processing.

    Extends ProjectionContext with canonical projection-specific fields.

    Attributes:
        strategy: Resolution strategy to use
        confidence_threshold: Minimum confidence for automatic resolution
    """

    strategy: CanonicalProjectionStrategy = CanonicalProjectionStrategy.HIGHEST_CONFIDENCE
    confidence_threshold: float = 0.7


class CanonicalProjectionResult(ProjectionResult):
    """Result of a canonical state projection operation.

    Attributes:
        updated_state: The updated canonical state with resolved values (key: value format)
        resolved_fields: Fields that were successfully resolved from interpretive state
        pending_fields: Fields that still need resolution (ambiguous/low confidence)
        validation_errors: Any validation errors encountered
        requires_confirmation: Fields that require user confirmation
        actions_triggered: List of actions that were triggered based on validation
    """

    updated_state: Any  # State - canonical state with resolved values
    resolved_fields: Dict[str, Any] = PydField(default_factory=dict)
    pending_fields: List[str] = PydField(default_factory=list)
    validation_errors: Dict[str, str] = PydField(default_factory=dict)
    requires_confirmation: Dict[str, Any] = PydField(default_factory=dict)
    actions_triggered: List[str] = PydField(default_factory=list)


class BaseProjectorCanonicalState(BaseProjector):
    """Abstract base class for Canonical State Projector implementations.

    The Canonical State Projector receives the interpretive state (with inference
    and value-confidence pairs) from the Mutator, validates constraints, and 
    produces the canonical state (with resolved values). It can also trigger 
    actions when validation passes.

    This can be implemented as:
    - A conventional function (rule-based, highest confidence, etc.)
    - An LLM-based resolver (for complex disambiguation)
    - A hybrid approach

    Example usage:
        class HighestConfidenceProjector(BaseProjectorCanonicalState):
            async def project(
                self,
                context: CanonicalProjectionContext
            ) -> CanonicalProjectionResult:
                # Start with current canonical state or create new one
                new_canonical_state = context.canonical_state.copy() if context.canonical_state else State()
                resolved = {}
                pending = []
                actions = []

                # Iterate through interpretive state fields
                for node_id, node in context.interpretive_state.nodes.items():
                    field_instance = node.value
                    if not field_instance.snapshots:
                        pending.append(node_id)
                        continue

                    # Get the latest snapshot with value-confidence pairs
                    latest = field_instance.snapshots[-1]
                    if not latest.value_confidence_list:
                        pending.append(node_id)
                        continue

                    # Find value with highest confidence
                    top_value = max(
                        latest.value_confidence_list,
                        key=lambda x: x.confidence
                    )

                    if top_value.confidence >= context.confidence_threshold:
                        # Validate the value
                        is_valid, error = await self.validate_value(
                            node_id, top_value.value, context.schema
                        )

                        if is_valid:
                            resolved[node_id] = top_value.value
                            # Check if action should be triggered
                            if self._should_trigger_action(context, node_id):
                                actions.append(f"action_{node_id}")
                        else:
                            pending.append(node_id)
                    else:
                        pending.append(node_id)

                return CanonicalProjectionResult(
                    updated_state=new_canonical_state,
                    resolved_fields=resolved,
                    pending_fields=pending,
                    actions_triggered=actions
                )
    """

    @abstractmethod
    async def project(
        self, context: CanonicalProjectionContext
    ) -> CanonicalProjectionResult:
        """Resolve interpretive state to canonical state and validate.

        This method analyzes the interpretive state with value-confidence pairs,
        validates constraints, and produces a canonical state with resolved values.
        Can also trigger actions when validation passes.

        Args:
            context: CanonicalProjectionContext with interpretive state and current canonical state

        Returns:
            CanonicalProjectionResult with updated canonical state and any triggered actions
        """
        pass

    @abstractmethod
    async def validate_value(
        self, field_key: str, value: Any, schema: Optional[Any] = None
    ) -> tuple[bool, Optional[str]]:
        """Validate a single value against schema constraints.

        Args:
            field_key: The field key being validated
            value: The value to validate
            schema: Optional schema for validation rules

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    async def can_trigger_action(
        self, context: CanonicalProjectionContext
    ) -> tuple[bool, Optional[str]]:
        """Check if current state allows triggering an action.

        Args:
            context: CanonicalProjectionContext with current states

        Returns:
            Tuple of (can_trigger, action_name)
        """
        pass

    def get_strategy(self) -> CanonicalProjectionStrategy:
        """Get the current canonical projection strategy.

        Override this method to return the appropriate strategy.

        Returns:
            The canonical projection strategy being used
        """
        return CanonicalProjectionStrategy.HIGHEST_CONFIDENCE


# =============================================================================
# Backward Compatibility Aliases (deprecated)
# =============================================================================

# Interpreter aliases
BaseInterpreter = BaseProjectorUI
InterpretationContext = UIProjectionContext
InterpretationResult = UIProjectionResult

# Canonicalizer aliases
BaseCanonicalizer = BaseProjectorCanonicalState
CanonicalizationContext = CanonicalProjectionContext
CanonicalizationResult = CanonicalProjectionResult
CanonicalizationStrategy = CanonicalProjectionStrategy
