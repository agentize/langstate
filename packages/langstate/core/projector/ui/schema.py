"""Pydantic schemas for UI Projector module.

This module contains all data models used by the UI Projector interface.
"""

from enum import Enum
from typing import Annotated, Dict, List

from pydantic import BaseModel, Field

from ..base.schema import ProjectionContext, ProjectionResult


class UIComponentType(str, Enum):
    """Type of UI component."""

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
    """UI component model."""

    component_type: Annotated[
        UIComponentType,
        Field(description="Type of the UI component"),
    ]
    field_id: Annotated[
        str,
        Field(description="Associated field identifier"),
    ]
    label: Annotated[
        str,
        Field(default="", description="Display label for the component"),
    ]
    placeholder: Annotated[
        str,
        Field(default="", description="Placeholder text"),
    ]
    options: Annotated[
        List[Dict[str, object]],
        Field(
            default_factory=list,
            description="Options for select/radio/checkbox components",
        ),
    ]
    validation_rules: Annotated[
        Dict[str, object],
        Field(default_factory=dict, description="Client-side validation rules"),
    ]
    disabled: Annotated[
        bool,
        Field(default=False, description="Whether the component is disabled"),
    ]
    required: Annotated[
        bool,
        Field(default=False, description="Whether the field is required"),
    ]
    metadata: Annotated[
        Dict[str, object],
        Field(default_factory=dict, description="Additional component metadata"),
    ]


class UIProjectionContext(ProjectionContext):
    """Context provided to the UI projector for processing.

    UI projector uses the shared ProjectionContext contract.
    """

    pass


class UIProjectionResult(ProjectionResult):
    """Result of a UI projection operation."""

    prompt: Annotated[
        str,
        Field(default="", description="The generated prompt/message for the user"),
    ]
    components: Annotated[
        List[UIComponent],
        Field(default_factory=list, description="List of UI components to display"),
    ]
    suggestions: Annotated[
        Dict[str, List[object]],
        Field(
            default_factory=dict, description="Suggested values/options for the user"
        ),
    ]
    is_complete: Annotated[
        bool,
        Field(default=False, description="Whether the form/flow is complete"),
    ]
    next_fields: Annotated[
        List[str],
        Field(default_factory=list, description="Fields to focus on next"),
    ]
