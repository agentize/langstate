from __future__ import annotations
import datetime
from typing import Any, Dict, List, Optional, Union, TypeAlias
from enum import Enum

from pydantic import BaseModel, Field as PydField
from .basic import FieldStatus, FieldValue, ValueType, Info
from .updater import Updater
from ..data_structure.dag import DirectedAcyclicGraphNode, DirectedAcyclicGraphEdge, DirectedAcyclicGraph
from .constraints import Constraint

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
    """
    FieldDependencyInstance represents a dependency instance with an associated confidence level.

    Attributes:
        id (str): A unique identifier for the dependency instance.
        dependency (Constraint): The constraint or condition that this dependency represents.
        match_confidence (float): A value between 0.0 and 1.0 indicating the confidence level 
            that the dependency is fulfilled. Higher values indicate greater confidence.
    """
    id: str
    dependency: Constraint
    match_confidence: float = PydField(..., ge=0.0, le=1.0)

"""
Defines the dependency relationship between fields.

The Constraint from FieldA to FieldB means:
Only when this Constraint is matched on FieldA, can FieldB be "talked" or interacted with.
"""
Schema: TypeAlias = DirectedAcyclicGraph[Field, Constraint]

State: TypeAlias = DirectedAcyclicGraph[FieldInstance, FieldDependencyInstance]

