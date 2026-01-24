"""Pydantic schemas for Schema Reader module.

This module contains all data models used by the Schema Reader interface.
"""

from enum import Enum
from typing import Annotated, Dict, Optional

from pydantic import BaseModel, Field, RootModel


class SourceType(str, Enum):
    """Type of schema source."""

    YAML = "yaml"
    JSON = "json"
    OPENAPI = "openapi"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class SchemaField(BaseModel):
    """Schema field definition."""

    field_id: Annotated[
        str,
        Field(description="Unique identifier for the field"),
    ]
    field_type: Annotated[
        str,
        Field(
            default="string",
            description="Data type of the field (string, integer, boolean, etc.)",
        ),
    ]
    label: Annotated[
        str,
        Field(default="", description="Human-readable label"),
    ]
    description: Annotated[
        str,
        Field(default="", description="Detailed description of the field"),
    ]
    required: Annotated[
        bool,
        Field(default=False, description="Whether the field is required"),
    ]
    default_value: Annotated[
        Optional[object],
        Field(default=None, description="Default value for the field"),
    ]
    validation_rules: Annotated[
        Dict[str, object],
        Field(default_factory=dict, description="Validation rules for the field"),
    ]
    metadata: Annotated[
        Dict[str, object],
        Field(default_factory=dict, description="Additional field metadata"),
    ]


class Schema(RootModel[Dict[str, SchemaField]]):
    """Schema definition model: simple key-value mapping of field definitions.

    Format: {key: SchemaField}

    Example:
        {
            "name": SchemaField(
                field_id="name",
                field_type="string",
                label="Full Name",
                required=True
            ),
            "email": SchemaField(
                field_id="email",
                field_type="string",
                label="Email Address",
                required=True
            )
        }
    """

    pass