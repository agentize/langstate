"""Interpreter interface for LangState.

The Interpreter is responsible for:
- Generating UI component mappings based on field schemas
- Producing LLM completions for the conversation
- Creating prompts and responses based on current state
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field as PydField, ConfigDict

if TYPE_CHECKING:
    from ..models.field import State


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


class InterpretationResult(BaseModel):
    """Result of an interpretation operation.

    Attributes:
        prompt: The generated prompt/message for the user
        components: List of UI components to display
        suggestions: Suggested values/actions for the user
        is_complete: Whether the form/flow is complete
        next_fields: Fields to focus on next
        metadata: Additional metadata
    """

    prompt: str = ""
    components: List[UIComponent] = PydField(default_factory=list)
    suggestions: Dict[str, List[Any]] = PydField(default_factory=dict)
    is_complete: bool = False
    next_fields: List[str] = PydField(default_factory=list)
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class InterpretationContext(BaseModel):
    """Context provided to the interpreter for processing.

    Attributes:
        current_state: Current interpretive state graph with field instances (includes value-confidence pairs)
        canonical_state: Canonical state with resolved values (business state, key:value only)
        schema: The schema definition
        conversation_history: Conversation history for context
        user_preferences: User preferences for UI generation
        metadata: Additional context metadata
    """

    current_state: Any  # State (Interpretive State)
    canonical_state: Optional[Any] = None  # State (Canonical/Business State)
    schema: Optional[Any] = None  # Schema
    conversation_history: List[Dict[str, str]] = PydField(default_factory=list)
    user_preferences: Dict[str, Any] = PydField(default_factory=dict)
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class BaseInterpreter(ABC):
    """Abstract base class for Interpreter implementations.

    The Interpreter generates UI components and LLM completions based on
    the current state graph. It bridges the gap between the internal state
    representation and what the user sees.

    Responsibilities:
    - Map field schemas to appropriate UI component types
    - Generate natural language prompts/responses
    - Suggest values based on context
    - Determine which fields to focus on next

    Example usage:
        class ChatInterpreter(BaseInterpreter):
            async def interpret(
                self,
                context: InterpretationContext
            ) -> InterpretationResult:
                # Generate components for unfilled fields
                components = []
                for node_id, node in context.current_state.nodes.items():
                    field_instance = node.value
                    # Check if field has resolved value
                    if not self._has_resolved_value(field_instance):
                        component = self.map_field_to_component(field_instance)
                        components.append(component)

                # Generate prompt
                prompt = await self.llm.generate_prompt(context)

                return InterpretationResult(
                    prompt=prompt,
                    components=components,
                    is_complete=context.canonical_state.is_complete
                )
    """

    @abstractmethod
    async def interpret(self, context: InterpretationContext) -> InterpretationResult:
        """Generate UI components and prompt based on current state.

        This method takes the current state and generates the appropriate
        UI representation and natural language prompt for the user.

        Args:
            context: InterpretationContext containing current state

        Returns:
            InterpretationResult with UI components and prompt
        """
        pass

    @abstractmethod
    async def generate_prompt(self, context: InterpretationContext) -> str:
        """Generate a natural language prompt for the user.

        Args:
            context: InterpretationContext containing current state

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

    @abstractmethod
    async def initialize(self, schema: Any) -> None:
        """Initialize the interpreter with a schema.

        This method is called when the interpreter is first set up,
        allowing it to configure itself based on the schema definition.

        Args:
            schema: The schema definition to use for interpretation
        """
        pass

    def get_supported_components(self) -> List[UIComponentType]:
        """Get list of supported UI component types.

        Override this method to specify which component types
        this interpreter supports.

        Returns:
            List of supported UIComponentType values
        """
        return list(UIComponentType)
