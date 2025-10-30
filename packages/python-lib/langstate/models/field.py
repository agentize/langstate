from __future__ import annotations
import datetime
from typing import Any, Dict, List, Optional, Union
try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias
from enum import Enum

from pydantic import BaseModel, Field as PydField, ConfigDict, field_validator
from .basic import FieldStatus, FieldValue, ValueType, Info, FieldStatusEnum
from .updater import Updater
from ..data_structure.dag import DirectedAcyclicGraphNode, DirectedAcyclicGraphEdge, DirectedAcyclicGraph
from .constraints import Constraint, utc_now

class Field(BaseModel):
    """Represents a field with its metadata, dependencies, and configuration.

    Attributes:
        id: A unique identifier for the field.
        info: Metadata information about the field.
        constraints: A list of constraints that define the relationships or rules
            applied to this field.
        default_value: The default value assigned to the field, if any.
        default_updaters: A list of updaters that can modify the field's value.
        tags: A list of tags for categorization or additional metadata.
    """
    id: str
    info: Info
    constraints: List[Constraint] = PydField(default_factory=list)
    default_value: Optional[FieldValue] = None
    default_updaters: List[Updater] = PydField(default_factory=list)
    tags: List[str] = PydField(default_factory=list)

    # Pydantic v2 style config: allow extra metadata and freeze instances by default
    model_config = ConfigDict(extra='allow', frozen=True)

class ValueConfidence(BaseModel):
    confidence: float = PydField(..., ge=-1.0, le=1.0)  # Confidence score [-1.0, 1.0]
    value: FieldValue

class FieldSnapshot(BaseModel):
    id: str
    status: FieldStatus
    value_confidences: List[ValueConfidence] = PydField(default_factory=list)
    timestamp: datetime.datetime = PydField(default_factory=utc_now)
    updater: Optional[Updater] = None
    meta_data: Dict[str, Any] = PydField(default_factory=dict)

    @field_validator("status", mode="before")
    @classmethod
    def coerce_status_enum(cls, v):  # type: ignore[override]
        # Support passing FieldStatusEnum values by converting to their string representation
        if isinstance(v, FieldStatusEnum):
            return v.value
        return v

class FieldInstance(BaseModel):
    """An instance of a Field with a specific value."""
    id: str
    field: Field
    snapshots: List[FieldSnapshot] = PydField(default_factory=list)

class FieldDependencyInstance(BaseModel):
    """
    FieldDependencyInstance represents a dependency instance with an associated confidence level.

    Attributes:
        id (str): A unique identifier for the dependency instance.
        dependency (Constraint): The constraint or condition that this dependency represents.
        match_confidence (float): A value between 0.0 and 1.0 indicating the confidence level 
            that the dependency is fulfilled. Higher values indicate greater confidence.
    """
    id: str
    dependencies: List[Constraint] = PydField(default_factory=list)
    match_confidence: float = PydField(..., ge=0.0, le=1.0)



class Schema(DirectedAcyclicGraph[Field, Constraint]):
    """
    Defines the dependency relationship between fields.

    The Constraint from FieldA to FieldB means:
    Only when this Constraint is matched on FieldA, can FieldB be "talked" or interacted with.
    """
    pass


class State(DirectedAcyclicGraph[FieldInstance, FieldDependencyInstance]):
    """
    Defines the state of the system, including all field instances and their dependencies.
    Each node represents a FieldInstance, and each edge represents a FieldDependencyInstance.
    """
    pass

