from __future__ import annotations
import datetime
from typing import Any, Dict, List, Optional, Union, TypeAlias
from enum import Enum

from pydantic import BaseModel, Field as PydField
from .basic import FieldStatus, Info
from .updater import Updater
from ..data_structure.dag import DirectedAcyclicGraphNode, DirectedAcyclicGraphEdge, DirectedAcyclicGraph
from .dependency import FieldDependency


FieldValue = Union[ bool, int, float, str ]

class FieldValueType(str, Enum):
    """
    FieldValueType is an enumeration that defines the possible types of values a field can have.

    Attributes:
        STRING: Represents a string value.
        INTEGER: Represents an integer value.
        NUMBER: Represents a numeric value (can include floats).
        BOOLEAN: Represents a boolean value (True or False).
        ARRAY: Represents an array value. The value will be the length of the array. 
               The content of the array is managed by a Directed Acyclic Graph (DAG) for dependencies.
        OBJECT: Represents an object value. The value will be a reference string. 
                The content of the object is managed by a Directed Acyclic Graph (DAG) for dependencies.
    """
    STRING   = "string"
    INTEGER  = "integer"
    NUMBER   = "number"
    BOOLEAN  = "boolean"
    ARRAY    = "array"
    OBJECT   = "object"

class Field(BaseModel):
    """Represents a field with its metadata, dependencies, and configuration."""
    id: str
    info: Info
    valid_value_types: List[FieldValueType]
    default_value: Optional[FieldValue] = None
    default_updaters: List[Updater] = PydField(default_factory=list)
    tags: List[str] = PydField(default_factory=list)

    class Config:
        """Configuration for Field model."""
        extra = "allow"

class ValueConfidence(BaseModel):
    confidence: float = PydField(..., ge=-1.0, le=1.0)  # Confidence score [-1.0, 1.0]
    value: FieldValue

class FieldSnapshot(BaseModel):
    id: str
    status: FieldStatus
    value_confidences: List[ValueConfidence] = PydField(default_factory=list)
    timestamp: datetime.datetime
    updater: Optional[Updater] = None
    meta_data: Dict[str, Any] = PydField(default_factory=dict)

class FieldInstance(BaseModel):
    """An instance of a Field with a specific value."""
    id: str
    field: Field
    snapshots: List[FieldSnapshot] = PydField(default_factory=list)

class FieldDependencyInstance(BaseModel):
    id: str
    dependency: FieldDependency
    value: FieldValue

Schema: TypeAlias = DirectedAcyclicGraph[Field, FieldDependency]
State: TypeAlias = DirectedAcyclicGraph[FieldInstance, FieldDependencyInstance]

