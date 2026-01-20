"""Pydantic schemas for LangState orchestrator module.

This module contains all data models used by the LangState orchestrator.
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from ...state.interpretive.schema import InterpretiveState
from ...state.canonical.schema import CanonicalState


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
    action_data: Dict[str, object] = Field(default_factory=dict)
    selection: List[object] = Field(default_factory=list)
    field_id: Optional[str] = None
    confirmed: Optional[bool] = None
    files: List[Dict[str, object]] = Field(default_factory=list)
    metadata: Dict[str, object] = Field(default_factory=dict)

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
        cls, action: str, data: Optional[Dict[str, object]] = None
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
        cls, selection: List[object], field_id: Optional[str] = None
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
        state: Current interpretive state
        canonical_state: Canonical state with resolved values (business state)
        pending_fields: Fields still needing values
        metadata: Additional metadata
    """

    interaction_type: InteractionType
    prompt: str = ""
    components: List[object] = Field(default_factory=list)
    options: Dict[str, List[object]] = Field(default_factory=dict)
    state: Optional[InterpretiveState] = None
    canonical_state: Optional[CanonicalState] = None
    pending_fields: List[str] = Field(default_factory=list)
    metadata: Dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)


class ActionResultData(BaseModel):
    """Result returned when the flow is complete and action can be taken.

    Attributes:
        state: Final interpretive state with all field snapshots
        canonical_state: Final canonical state with resolved values for action
        success: Whether the flow completed successfully
        action_data: Data to be used for the action
        metadata: Additional metadata
    """

    state: InterpretiveState
    canonical_state: CanonicalState
    success: bool = True
    action_data: Dict[str, object] = Field(default_factory=dict)
    metadata: Dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)


class LangStateConfig(BaseModel):
    """Configuration for LangState instance.

    Attributes:
        schema_source: Path or dict for schema definition
        confidence_threshold: Minimum confidence for auto-canonicalization
        require_confirmation: Whether to require user confirmation for values
        conversation_history_limit: Max conversation history to maintain
        metadata: Additional configuration
    """

    schema_source: Optional[str] = None
    confidence_threshold: float = 0.7
    require_confirmation: bool = False
    conversation_history_limit: int = 100
    metadata: Dict[str, object] = Field(default_factory=dict)
