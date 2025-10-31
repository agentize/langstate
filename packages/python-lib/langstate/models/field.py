from __future__ import annotations
import datetime
from typing import Any, Dict, List, Optional, Union
try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias
from enum import Enum

from pydantic import BaseModel, Field as PydField, ConfigDict, field_validator
from .basic import PropertyStatus, PropertyValue, ValueType, Info, PropertyStatusEnum
from .updater import Updater
from ..data_structure.dag import DirectedAcyclicGraphNode, DirectedAcyclicGraphEdge, DirectedAcyclicGraph
from .constraints import Constraint, utc_now

class Property(BaseModel):
    """Represents a property with its metadata, dependencies, and configuration.

    Attributes:
        id: A unique identifier for the property.
        info: Metadata information about the property.
        constraints: A list of constraints that define the relationships or rules
            applied to this property.
        default_value: The default value assigned to the property, if any.
        default_updaters: A list of updaters that can modify the property's value.
        tags: A list of tags for categorization or additional metadata.
    """
    id: str
    info: Info
    constraints: List[Constraint] = PydField(default_factory=list)
    default_value: Optional[PropertyValue] = None
    default_updaters: List[Updater] = PydField(default_factory=list)
    tags: List[str] = PydField(default_factory=list)

    # Pydantic v2 style config: allow extra metadata and freeze instances by default
    model_config = ConfigDict(extra='allow', frozen=True)

class ValueConfidence(BaseModel):
    confidence: float = PydField(..., ge=-1.0, le=1.0)  # Confidence score [-1.0, 1.0]
    value: PropertyValue

class PropertySnapshot(BaseModel):
    id: str
    status: PropertyStatus
    value_confidences: List[ValueConfidence] = PydField(default_factory=list)
    timestamp: datetime.datetime = PydField(default_factory=utc_now)
    updater: Optional[Updater] = None
    meta_data: Dict[str, Any] = PydField(default_factory=dict)

    @field_validator("status", mode="before")
    @classmethod
    def coerce_status_enum(cls, v):  # type: ignore[override]
        # Support passing PropertyStatusEnum values by converting to their string representation
        if isinstance(v, PropertyStatusEnum):
            return v.value
        return v

class PropertyInstance(BaseModel):
    """An instance of a Property with a specific value."""
    id: str
    property: Property
    snapshots: List[PropertySnapshot] = PydField(default_factory=list)

class PropertyDependencyInstance(BaseModel):
    """
    PropertyDependencyInstance represents a dependency instance with an associated confidence level.

    Attributes:
        id (str): A unique identifier for the dependency instance.
        dependency (Constraint): The constraint or condition that this dependency represents.
        match_confidence (float): A value between 0.0 and 1.0 indicating the confidence level 
            that the dependency is fulfilled. Higher values indicate greater confidence.
    """
    id: str
    dependencies: List[Constraint] = PydField(default_factory=list)
    match_confidence: float = PydField(..., ge=0.0, le=1.0)



class Schema(DirectedAcyclicGraph[Property, Constraint]):
    """
    Defines the dependency relationship between properties.

    The Constraint from PropertyA to PropertyB means:
    Only when this Constraint is matched on PropertyA, can PropertyB be "talked" or interacted with.
    """
    pass


class State(DirectedAcyclicGraph[PropertyInstance, PropertyDependencyInstance]):
    """
    Defines the state of the system, including all property instances and their dependencies.
    Each node represents a PropertyInstance, and each edge represents a PropertyDependencyInstance.
    """
    pass

