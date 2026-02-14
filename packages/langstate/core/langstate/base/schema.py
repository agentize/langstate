"""Pydantic schemas for LangState orchestrator module.

This module contains all data models used by the LangState orchestrator.
"""

from enum import Enum
from typing import Annotated, Dict, List, Optional

from pydantic import BaseModel, Field

from ...state.schema import StateSchema


class InputType(str, Enum):
    """Type of input received from the user/client."""

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

    input_type: Annotated[
        InputType,
        Field(default=InputType.TEXT, description="Type of input being provided"),
    ]
    text: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Text content (for TEXT type or accompanying other types)",
        ),
    ]

    action: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Action identifier (for ACTION type, e.g., button_id, form_name)",
        ),
    ]

    action_data: Annotated[
        Optional[Dict[str, object]],
        Field(
            default=None,
            description="Additional data for the action (form fields, parameters)",
        ),
    ]

    selection: Annotated[
        Optional[List[object]],
        Field(default=None, description="Selected option(s) for SELECTION type"),
    ]

    field_id: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Target field identifier (if input is for a specific field)",
        ),
    ]

    confirmed: Annotated[
        Optional[bool],
        Field(default=None, description="Confirmation status for CONFIRMATION type"),
    ]

    files: Annotated[
        Optional[List[Dict[str, object]]],
        Field(default=None, description="List of file references for FILE type"),
    ]

    metadata: Annotated[
        Optional[Dict[str, object]],
        Field(default=None, description="Additional context or metadata"),
    ]

    @classmethod
    def from_text(cls, text: str) -> "AgentInput":
        """Create AgentInput from simple text string.

        Args:
            text: The text input

        Returns:
            AgentInput instance with TEXT type
        """
        return cls(
            input_type=InputType.TEXT,
            text=text,
            action=None,
            action_data=None,
            selection=None,
            field_id=None,
            confirmed=None,
            files=None,
            metadata=None,
        )

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
            text=None,
            action=action,
            action_data=data,
            selection=None,
            field_id=None,
            confirmed=None,
            files=None,
            metadata=None,
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
            text=None,
            action=None,
            action_data=None,
            selection=selection,
            field_id=field_id,
            confirmed=None,
            files=None,
            metadata=None,
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
            text=None,
            action=None,
            action_data=None,
            selection=None,
            field_id=field_id,
            confirmed=confirmed,
            files=None,
            metadata=None,
        )

    def is_empty(self) -> bool:
        """Check if the input is effectively empty (initial invocation).

        Returns:
            True if this represents an empty/initial input
        """
        return (
            self.text is None
            and self.action is None
            and (self.selection is None or len(self.selection) == 0)
            and self.confirmed is None
            and (self.files is None or len(self.files) == 0)
        )


class InteractionType(str, Enum):
    """Type of interaction required from the user."""

    PROMPT = "prompt"
    SELECTION = "selection"
    CONFIRMATION = "confirmation"
    ACTION = "action"
    COMPLETE = "complete"


class InteractionRequest(BaseModel):
    """Request object returned when LangState needs user interaction.

    This is what developers receive when LangState needs input from the user.
    Developers can send this to their frontend via HTTP or other means.
    """

    interaction_type: Annotated[
        InteractionType,
        Field(description="Type of interaction needed"),
    ]
    prompt: Annotated[
        str,
        Field(default="", description="Message/prompt for the user"),
    ]
    components: Annotated[
        List[object],
        Field(default_factory=list, description="UI components to render"),
    ]
    options: Annotated[
        Dict[str, List[object]],
        Field(
            default_factory=dict, description="Options for selection-type interactions"
        ),
    ]
    state: Annotated[
        Optional[StateSchema],
        Field(default=None, description="Current state snapshot"),
    ]
    pending_fields: Annotated[
        List[str],
        Field(default_factory=list, description="Fields still needing values"),
    ]
    metadata: Annotated[
        Dict[str, object],
        Field(default_factory=dict, description="Additional metadata"),
    ]


class StateResultData(BaseModel):
    """Result returned when the flow is complete."""

    state: Annotated[
        StateSchema,
        Field(description="Final state with all field snapshots"),
    ]
    success: Annotated[
        bool,
        Field(default=True, description="Whether the flow completed successfully"),
    ]
    data: Annotated[
        Dict[str, object],
        Field(default_factory=dict, description="Additional output data"),
    ]
    metadata: Annotated[
        Dict[str, object],
        Field(default_factory=dict, description="Additional metadata"),
    ]


class LangStateConfig(BaseModel):
    """Configuration for LangState instance."""

    schema_source: Annotated[
        Optional[str],
        Field(default=None, description="Path or dict for schema definition"),
    ]
    confidence_threshold: Annotated[
        float,
        Field(default=0.7, description="Default confidence threshold for projection"),
    ]
    require_confirmation: Annotated[
        bool,
        Field(
            default=False, description="Whether to require user confirmation for values"
        ),
    ]
    conversation_history_limit: Annotated[
        int,
        Field(default=100, description="Max conversation history to maintain"),
    ]
    metadata: Annotated[
        Dict[str, object],
        Field(default_factory=dict, description="Additional configuration"),
    ]
