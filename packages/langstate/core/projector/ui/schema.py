"""Pydantic schemas for UI Projector module.

This module contains all data models used by the UI Projector interface.
"""

from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field, ConfigDict

from ..base.schema import ProjectionContext, ProjectionResult


class UIComponentType(str, Enum):
    """Type of UI component.

    Attributes:
        TEXT_INPUT: Free-form text input field
        SELECT: Dropdown/select component
        RADIO: Radio button group
        CHECKBOX: Checkbox or checkbox group
        DATE_PICKER: Date selection component
        TIME_PICKER: Time selection component
        FILE_UPLOAD: File upload component
        BUTTON: Action button
        TEXTAREA: Multi-line text input
        NUMBER_INPUT: Numeric input field
        SLIDER: Range slider
        TOGGLE: On/off toggle switch
        AUTOCOMPLETE: Autocomplete/suggestion input
        CUSTOM: Custom component type
    """

    TEXT_INPUT = "text_input"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    DATE_PICKER = "date_picker"
    TIME_PICKER = "time_picker"
    FILE_UPLOAD = "file_upload"
    BUTTON = "button"
    TEXTAREA = "textarea"
    NUMBER_INPUT = "number_input"
    SLIDER = "slider"
    TOGGLE = "toggle"
    AUTOCOMPLETE = "autocomplete"
    CUSTOM = "custom"


class UIComponent(BaseModel):
    """UI component model.

    Attributes:
        component_type: Type of the UI component
        field_id: Associated field identifier
        label: Display label for the component
        placeholder: Placeholder text
        options: Options for select/radio/checkbox components
        validation_rules: Client-side validation rules
        disabled: Whether the component is disabled
        required: Whether the field is required
        metadata: Additional component metadata
    """

    component_type: UIComponentType
    field_id: str
    label: str = ""
    placeholder: str = ""
    options: List[Dict[str, object]] = Field(default_factory=list)
    validation_rules: Dict[str, object] = Field(default_factory=dict)
    disabled: bool = False
    required: bool = False
    metadata: Dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class UIProjectionContext(ProjectionContext):
    """Context provided to the UI projector for processing.

    Extends ProjectionContext with UI-specific fields.

    Attributes:
        conversation_history: Conversation history for context
        user_preferences: User preferences for UI generation
    """

    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    user_preferences: Dict[str, object] = Field(default_factory=dict)


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
    components: List[UIComponent] = Field(default_factory=list)
    suggestions: Dict[str, List[object]] = Field(default_factory=dict)
    is_complete: bool = False
    next_fields: List[str] = Field(default_factory=list)
