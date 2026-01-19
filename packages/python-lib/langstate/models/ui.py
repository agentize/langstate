"""UI models for LangState.

This module contains data models for UI representation,
used by ProjectorUI to generate user interface components.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field as PydField, ConfigDict


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


__all__ = [
    "UIComponentType",
    "UIComponent",
]
