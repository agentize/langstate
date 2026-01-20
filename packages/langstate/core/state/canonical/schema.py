"""Pydantic schemas for Canonical State module.

This module contains all data models used by the Canonical State.
Canonical State uses simple key-value format for business logic.
"""

from typing import Dict, Optional

from pydantic import BaseModel, Field, ConfigDict


class CanonicalFieldState(BaseModel):
    """Canonical state for a single field (simple key-value).

    Attributes:
        field_id: Unique identifier for the field
        value: The resolved value for the field
        metadata: Additional field metadata
    """

    field_id: str
    value: Optional[object] = None
    metadata: Dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class CanonicalStateData(BaseModel):
    """Data model for the entire canonical state.

    Attributes:
        fields: Dictionary of field_id to CanonicalFieldState
        metadata: Additional state metadata
    """

    fields: Dict[str, CanonicalFieldState] = Field(default_factory=dict)
    metadata: Dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")
