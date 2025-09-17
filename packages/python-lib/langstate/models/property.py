from __future__ import annotations
import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field
from .basic import Info
from .agent import Agent
from ..utils import Tree


class TouchState(str, Enum):
    """Enumeration representing the different status types of a property."""
    UNTOUCHED = "untouched"
    GENERATED = "generated"
    EDITED = "edited"
    VALIDATED = "validated"
    UNKNOWN = "unknown"
    CUSTOM = "custom"


class EnumerationCondition(BaseModel):
    """Condition that specifies allowed values through enumeration."""
    values: List[Any]

class ValueRangeCondition(BaseModel):
    """Condition that specifies allowed values through a numeric range."""
    min: float
    max: float

class ValueSimilarityCondition(BaseModel):
    """Condition that specifies allowed values based on similarity to a reference."""
    reference: str
    threshold: float  # Similarity threshold (0-1.0)

class StatusTypeCondition(BaseModel):
    """Condition that specifies allowed and disallowed status types."""
    allowed_touch_state: List[TouchState]
    disallowed_touch_state: List[TouchState]

class PromptCondition(BaseModel):
    """Condition that uses a prompt for evaluation."""
    prompt: str  # The prompt to be used for this condition

class PropertyDependency(BaseModel):
    """Defines a dependency relationship between properties with various condition types. It's OR relationship between any of two items"""
    property_id: str
    enumerationCondition: Optional[EnumerationCondition] = None
    valueRangeCondition: Optional[ValueRangeCondition] = None
    valueSimilarityCondition: Optional[ValueSimilarityCondition] = None
    statusTypeCondition: Optional[StatusTypeCondition] = None
    promptCondition: Optional[PromptCondition] = None
    
    class Config:
        """Configuration for PropertyDependency model."""
        extra = "allow"

PropertyValue = Union[
    None, bool, int, float, str,
    List["PropertyValue"],
    Dict[str, "PropertyValue"],
    "Property",  
]
class PropertyValueType(str, Enum):
    STRING   = "string"
    INTEGER  = "integer"
    NUMBER   = "number"
    BOOLEAN  = "boolean"
    NULL     = "null"
    ARRAY    = "array"
    OBJECT   = "object"
    PROPERTY = "property"

class PromptTemplate(BaseModel):
    """Template for generating prompts used in property processing."""
    id: str
    info: Info
    # Template for generating the property value without considering an existing value
    generate: Optional[str] = None
    # Template for updating the property value considering an existing value
    update: Optional[str] = None


class Property(Tree["Property", "PropertyValue"]):
    """Represents a property with its metadata, dependencies, and configuration."""
    id: str
    info: Info
    prompt_template: PromptTemplate | str | None = None
    value_type: PropertyValueType
    depends_on: List[PropertyDependency] = [] # AND relationship between items
    tags: List[str] = []

    class Config:
        """Configuration for Property model."""
        extra = "allow"

class PropertyState(BaseModel):
    """Represents the value of a property."""
    property_id: str
    property: Optional[Property] = None
    value: Union[str, int, float, bool, None]

class Touch(BaseModel):
    property_states: List["PropertyState"]
    requested_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    requested_by: List[Agent] = []
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_by: List[Agent] = []
