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

    field_id: Annotated[str, Field(description="Unique identifier for the field")]
    field_type: Annotated[
        str,
        Field(description="Data type of the field (string, integer, boolean, etc.)"),
    ] = "string"
    label: Annotated[str, Field(description="Human-readable label")] = ""
    description: Annotated[
        str, Field(description="Detailed description of the field")
    ] = ""
    required: Annotated[bool, Field(description="Whether the field is required")] = (
        False
    )
    default_value: Annotated[
        Optional[object], Field(description="Default value for the field")
    ] = None
    validation_rules: Annotated[
        Dict[str, object],
        Field(description="Validation rules for the field"),
    ] = {}
    metadata: Annotated[
        Dict[str, object],
        Field(description="Additional field metadata"),
    ] = {}


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
