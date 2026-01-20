"""Pydantic schemas for Schema Reader module.

This module contains all data models used by the Schema Reader interface.
"""

from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field, ConfigDict


class SourceType(str, Enum):
    """Type of schema source.

    Attributes:
        YAML: YAML file format
        JSON: JSON file format
        OPENAPI: OpenAPI specification
        CUSTOM: Custom schema format
        UNKNOWN: Unknown source type
    """

    YAML = "yaml"
    JSON = "json"
    OPENAPI = "openapi"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class SchemaField(BaseModel):
    """Schema field definition.

    Attributes:
        field_id: Unique identifier for the field
        field_type: Data type of the field (string, integer, boolean, etc.)
        label: Human-readable label
        description: Detailed description of the field
        required: Whether the field is required
        default_value: Default value for the field
        validation_rules: Validation rules for the field
        metadata: Additional field metadata
    """

    field_id: str
    field_type: str = "string"
    label: str = ""
    description: str = ""
    required: bool = False
    default_value: Optional[object] = None
    validation_rules: Dict[str, object] = Field(default_factory=dict)
    metadata: Dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class Schema(BaseModel):
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

    __root__: Dict[str, SchemaField]


class SchemaReadResult(BaseModel):
    """Result of reading a schema.

    Attributes:
        schema: The parsed schema
        source_type: Type of source (yaml, json, openapi, etc.)
        metadata: Additional metadata
    """

    schema: Schema
    source_type: SourceType = SourceType.UNKNOWN
    metadata: Dict[str, object] = Field(default_factory=dict)
