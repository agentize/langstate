
from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Union, TypeAlias
from .basic import FieldStatus

class EnumerationCondition(BaseModel):
    """Condition that specifies allowed values through enumeration."""
    values: List[Any]

class ValueRangeCondition(BaseModel):
    """Condition that specifies allowed values through a numeric range."""
    min: float
    max: float
    inclusive_min: bool = True
    inclusive_max: bool = True

class ValueSimilarityCondition(BaseModel):
    """Condition that specifies allowed values based on similarity to a reference."""
    reference: str
    threshold: float  # Similarity threshold (0-1.0)

class FieldStatusCondition(BaseModel):
    """Condition that specifies allowed and disallowed status types."""
    allowed_status: List[FieldStatus]
    disallowed_status: List[FieldStatus]

class PromptCondition(BaseModel):
    """Condition that uses a prompt for evaluation."""
    prompt: str  # The prompt to be used for this condition

class FieldDependency(BaseModel):
    """Defines a dependency relationship between fields with various condition types. It's OR relationship between any of two items"""
    property_id: str
    enumerationCondition: Optional[EnumerationCondition] = None
    valueRangeCondition: Optional[ValueRangeCondition] = None
    valueSimilarityCondition: Optional[ValueSimilarityCondition] = None
    statusCondition: Optional[FieldStatusCondition] = None
    promptCondition: Optional[PromptCondition] = None
    
    class Config:
        """Configuration for FieldDependency model."""
        extra = "allow"