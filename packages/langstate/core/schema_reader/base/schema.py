"""Pydantic schemas for Schema Reader module.

This module contains all data models used by the Schema Reader interface.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


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
    """Schema definition model.

    Attributes:
        schema_id: Unique identifier for the schema
        name: Human-readable name
        description: Detailed description of the schema
        version: Schema version
        fields: Dictionary of field definitions
        dependencies: Field dependencies (field_id -> list of dependent field_ids)
        metadata: Additional schema metadata
    """

    schema_id: str = ""
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    fields: Dict[str, SchemaField] = Field(default_factory=dict)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    metadata: Dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class SchemaReadResult(BaseModel):
    """Result of reading a schema.

    Attributes:
        schema: The parsed schema
        source_type: Type of source (yaml, json, openapi, etc.)
        source_path: Path or identifier of the source
        warnings: Any warnings during parsing
        metadata: Additional metadata
    """

    schema: Schema
    source_type: str = "unknown"
    source_path: str = ""
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")
