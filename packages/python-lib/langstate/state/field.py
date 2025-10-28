from __future__ import annotations
import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field
from .basic import Info
from .updater import Updater
from .agent import Agent
from ..utils import TreeNode


class TouchState(str, Enum):
    """Enumeration representing the different status types of a field."""
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

class FieldDependency(BaseModel):
    """Defines a dependency relationship between fields with various condition types. It's OR relationship between any of two items"""
    property_id: str
    enumerationCondition: Optional[EnumerationCondition] = None
    valueRangeCondition: Optional[ValueRangeCondition] = None
    valueSimilarityCondition: Optional[ValueSimilarityCondition] = None
    statusTypeCondition: Optional[StatusTypeCondition] = None
    promptCondition: Optional[PromptCondition] = None
    
    class Config:
        """Configuration for FieldDependency model."""
        extra = "allow"

FieldValue = Union[
    None, bool, int, float, str,
    List["FieldValue"],
    Dict[str, "FieldValue"],
    "Field",  
]
class FieldValueType(str, Enum):
    STRING   = "string"
    INTEGER  = "integer"
    NUMBER   = "number"
    BOOLEAN  = "boolean"
    NULL     = "null"
    ARRAY    = "array"
    OBJECT   = "object"
    FIELD = "field"


class Field(BaseModel):
    """Represents a field with its metadata, dependencies, and configuration."""
    id: str
    info: Info
    valid_value_types: List[FieldValueType]
    dependencies: List[FieldDependency] = [] # AND relationship between items
    default_updaters: List[Updater] = []
    tags: List[str] = []
    class Config:
        """Configuration for Field model."""
        extra = "allow"

class FieldInstance(BaseModel):
    """An instance of a Field with a specific value."""
    field: Field
    value: FieldValue

class Schema(TreeNode["Field"]):
    """Represents a schema containing fields and nested schemas."""
    id: str
    info: Info
    fields: List[Field] = []

class State(TreeNode["FieldInstance"]):
    """Represents the value of a field."""
    property_id: str
    property: Optional[Field] = None
    value: Union[str, int, float, bool, None]
    

class Touch(BaseModel):
    property_states: List["PropertyState"]
    requested_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    requested_by: List[Agent] = []
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_by: List[Agent] = []
