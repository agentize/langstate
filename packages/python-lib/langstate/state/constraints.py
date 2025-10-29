from pydantic import BaseModel, Field as PydField
from typing import Any, Dict, List, Optional, Union, TypeAlias, Generic, TypeVar
from .basic import FieldStatus, ValueType

T = TypeVar("T")

class AllowDisallowCondition(Generic[T], BaseModel):
    """
    Generic class for allow/disallow logic.

    Evaluation policy:
    1) If `allowed` is NON-EMPTY:
        -> Only items in `allowed` are allowed. `disallowed` is ignored.
    2) Else:
        -> All items allowed EXCEPT those in `disallowed`.
    3) Both empty -> all items allowed.

    Notes:
    - If an item is in both lists, it is ALLOWED when `allowed` is non-empty.
    - Prefer omitting an item from `allowed` if you want to block it while using an allowlist.
    """
    allowed: List[T] = PydField(default_factory=list)
    disallowed: List[T] = PydField(default_factory=list)

    def matches(self, value: T) -> bool:
        """
        Check if a given value matches the allow/disallow condition.

        :param value: The value to check.
        :return: True if the value matches the condition, False otherwise.
        """
        if self.allowed:
            return value in self.allowed
        return value not in self.disallowed

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

class FieldStatusCondition(AllowDisallowCondition[FieldStatus]):
    """
    Condition to gate by field status using allow/disallow lists.
    """
    pass

class FieldTypeCondition(AllowDisallowCondition[ValueType]):
    """
    Condition to gate by field value types using allow/disallow lists.
    """
    pass

class PromptCondition(BaseModel):
    """Condition that uses a prompt for evaluation."""
    prompt: str  # The prompt to be used for this condition

class Constraint(BaseModel):
    """A constraint applied to a field based on various conditions."""
    field_id: str
    fieldTypeCondition: Optional[FieldTypeCondition] = None
    enumerationCondition: Optional[EnumerationCondition] = None
    valueRangeCondition: Optional[ValueRangeCondition] = None
    valueSimilarityCondition: Optional[ValueSimilarityCondition] = None
    statusCondition: Optional[FieldStatusCondition] = None
    promptCondition: Optional[PromptCondition] = None
    
    class Config:
        """Configuration for Constraint model."""
        extra = "allow"