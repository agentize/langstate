from pydantic import BaseModel, Field as PydField
from typing import Any, Dict, List, Optional, Union, TypeAlias
from .basic import FieldStatus, ValueType

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
    """
    Gate by field status using allow/deny lists.

    Evaluation policy (deterministic, simple):
    1) If `allowed_status` is NON-EMPTY:
        -> Only statuses present in `allowed_status` are allowed.
            `disallowed_status` is IGNORED entirely in this case.
    2) Else (no allowed_status):
        -> All statuses are allowed EXCEPT those present in `disallowed_status`.
    3) If both lists are empty:
        -> All statuses are allowed.

    Implications:
    - If a status appears in BOTH lists, it is ALLOWED when `allowed_status` is non-empty
    (because allowlist is authoritative).
    - To block something while using an allowlist, simply omit it from `allowed_status`.

    Examples:
    - allowed=[READY, STABLE], disallowed=[DEPRECATED]  -> only READY/STABLE are allowed.
    - allowed=[], disallowed=[INVALID]                  -> everything except INVALID is allowed.
    - allowed=[], disallowed=[]                         -> all statuses allowed.
    """
    allowed_status: List[FieldStatus] = PydField(default_factory=list)
    disallowed_status: List[FieldStatus] = PydField(default_factory=list)


class FieldTypeCondition(BaseModel):
    """
    Gate by field value types using allow/deny lists.

    Same policy as FieldStatusCondition:
    1) If `allowed_types` is NON-EMPTY:
        -> Only types in `allowed_types` are allowed. `disallowed_types` is ignored.
    2) Else:
        -> All types allowed EXCEPT those in `disallowed_types`.
    3) Both empty -> all types allowed.

    Notes:
    - If a type is in both lists, it is ALLOWED when `allowed_types` is non-empty.
    - Prefer omitting a type from `allowed_types` if you want to block it while using an allowlist.
    """
    # Use your actual enum: FieldValueType (you had a naming slip: ValueType vs FieldValueType)
    allowed_types: List[ValueType] = PydField(default_factory=list)
    disallowed_types: List[ValueType] = PydField(default_factory=list)

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