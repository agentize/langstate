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
        Field(description="Display label for the component"),
    ] = ""
    placeholder: Annotated[
        str,
        Field(description="Placeholder text"),
    ] = ""
    options: Annotated[
        List[Dict[str, object]],
        Field(
            description="Options for select/radio/checkbox components",
        ),
    ] = []
    validation_rules: Annotated[
        Dict[str, object],
        Field(description="Client-side validation rules"),
    ] = Field(default_factory=dict)
    disabled: Annotated[
        bool,
        Field(description="Whether the component is disabled"),
    ] = False
    required: Annotated[
        bool,
        Field(description="Whether the field is required"),
    ] = False
    metadata: Annotated[
        Dict[str, object],
        Field(description="Additional component metadata"),
    ] = Field(default_factory=dict)


class UIProjectionContext(ProjectionContext):
    """Context provided to the UI projector for processing.

    UI projector uses the shared ProjectionContext contract.
    """

    pass


class UIProjectionResult(ProjectionResult):
    """Result of a UI projection operation."""

    prompt: Annotated[
        str,
        Field(description="The generated prompt/message for the user"),
    ] = ""
    components: Annotated[
        List[UIComponent],
        Field(description="List of UI components to display"),
    ] = []
    suggestions: Annotated[
        Dict[str, List[object]],
        Field(description="Suggested values/options for the user"),
    ] = Field(default_factory=dict)
    is_complete: Annotated[
        bool,
        Field(description="Whether the form/flow is complete"),
    ] = False
    next_fields: Annotated[
        List[str],
        Field(description="Fields to focus on next"),
    ] = Field(default_factory=list)
