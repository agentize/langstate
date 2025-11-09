from __future__ import annotations
import datetime
from typing import Any, Dict, List, Optional, Union
try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias
from enum import Enum

from pydantic import BaseModel, Field as PydField, ConfigDict, field_validator
from .basic import FieldStatus, FieldValue, Info, FieldStatusEnum
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
    top_n: int
    default_updaters: List[Updater] = PydField(default_factory=list)
    tags: List[str] = PydField(default_factory=list)

    # Pydantic v2 style config: allow extra metadata and freeze instances by default
    model_config = ConfigDict(extra='allow', frozen=True)
    
    def to_dag_node_name(self) -> str:
        """Return a string representation of this Field for DAG visualization.
        
        Returns:
            String label for this field node in DAG visualizations (format: id:type)
        """
        # Extract type from field_type constraint if available
        type_str = None
        if self.constraints:
            for constraint in self.constraints:
                if getattr(constraint, 'field_type', None) and constraint.field_type.allowed:
                    # Get the first allowed type
                    types = [t.value for t in constraint.field_type.allowed]
                    if types:
                        type_str = types[0]
                        break
        
        if type_str:
            return f"{self.id}:{type_str}"
        return self.id

class ValueConfidence(BaseModel):
    score: float = PydField(..., ge=-1.0, le=1.0)  # Confidence score [-1.0, 1.0]
    value: FieldValue

class FieldSnapshot(BaseModel):
    id: str
    status: FieldStatus
    value_confidence_list: List[ValueConfidence] = PydField(default_factory=list)
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
    property: Field
    snapshots: List[FieldSnapshot] = PydField(default_factory=list)

class ConstraintSnapshot(BaseModel):
    """
    Represents a snapshot of a constraint at a specific point in time.

    Attributes:
        id (str): A unique identifier for the constraint snapshot.
        constraint (Constraint): The constraint being captured in this snapshot.
        confidence (float): A value between 0.0 and 1.0 indicating the confidence level
            that the constraint is satisfied.
        timestamp (datetime.datetime): The time when the snapshot was taken.
        meta_data (Dict[str, Any]): Additional metadata associated with the snapshot.
    """
    id: str
    constraint: Constraint
    confidence: float = PydField(..., ge=0.0, le=1.0)
    timestamp: datetime.datetime = PydField(default_factory=utc_now)
    meta_data: Dict[str, Any] = PydField(default_factory=dict)


class ConstraintInstance(BaseModel):
    """
    ConstraintInstance represents a dependency instance with an associated confidence level.

    Attributes:
        id (str): A unique identifier for the dependency instance.
    constraint (Constraint): The constraint or condition that this dependency represents.
        confidence (float): A value between 0.0 and 1.0 indicating the confidence level
            that the dependency is fulfilled. Higher values indicate greater confidence.
    """
    id: str
    constraints: List[Constraint] = PydField(default_factory=list)
    snapshots: List[ConstraintSnapshot] = PydField(default_factory=list)

class Schema(DirectedAcyclicGraph[Field, Constraint]):
    """
    Defines a schema as a directed acyclic graph (DAG) of fields and their constraints.
    Each node represents a Field, and each edge represents a Constraint.
    """
    pass

class State(DirectedAcyclicGraph[FieldInstance, ConstraintInstance]):
    """
    Defines the state of the system, including all field instances and their dependencies.
    Each node represents a FieldInstance, and each edge represents a ConstraintInstance.
    """
    pass

