"""Formation and form model definitions.

This module contains models for representing forms and formations,
which are collections of properties and metadata used in the langstate system.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from .property import Property, Touch
from .basic import Info

class Form(BaseModel):
    """A form containing properties and metadata.
    
    Forms represent a collection of property snapshots with associated
    information and metadata.
    """
    id: str = Field(..., description="Unique identifier for the form")
    info: Info
    properties: List[PropertySnapshot] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for the form"
    )

class Formation(BaseModel):
    """A formation representing a structured collection of properties.
    
    Formations contain both perceived property snapshots and actual properties,
    along with descriptive information and metadata.
    """
    id: str = Field(..., description="Unique identifier for the formation")
    perceived: List[PropertySnapshot] = Field(default_factory=list)
    description: Optional[str] = Field(None, description="Description of the formation")
    properties: List[Property] = Field(..., description="The properties this formation applies to")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for the formation"
    )
