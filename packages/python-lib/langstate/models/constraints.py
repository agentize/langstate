from pydantic import BaseModel, Field as PydField, ConfigDict, field_validator, model_validator
from typing import Any, Dict, List, Optional, Union, Generic, TypeVar, TYPE_CHECKING
try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias
from datetime import datetime, timezone
from .basic import FieldStatus, Info, ValueType

T = TypeVar("T")


def utc_now() -> datetime:
    """Return current datetime in UTC timezone."""
    return datetime.now(timezone.utc)

class ConstraintCondition(BaseModel):
    """A generic constraint condition that can encapsulate various types of conditions."""
    info: Info

class AllowDisallowCondition(Generic[T], ConstraintCondition):
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

class EnumerationCondition(ConstraintCondition):
    """Condition that specifies allowed values through enumeration."""
    values: List[Any]

class RangeCondition(ConstraintCondition):
    """Condition that specifies allowed values through a numeric range."""
    min: float
    max: float
    inclusive_min: bool = True
    inclusive_max: bool = True
    
    @field_validator('max')
    @classmethod
    def validate_range(cls, v: float, info) -> float:
        """Ensure max >= min."""
        if 'min' in info.data and v < info.data['min']:
            raise ValueError(f"max ({v}) must be greater than or equal to min ({info.data['min']})")
        return v

class ValueSimilarityCondition(ConstraintCondition):
    """Condition that specifies allowed values based on similarity to a reference."""
    reference: str
    threshold: float = PydField(ge=0.0, le=1.0)  # Similarity threshold (0-1.0)

class StatusCondition(AllowDisallowCondition[FieldStatus]):
    """
    Condition to gate by property status using allow/disallow lists.

    Accepts values as either strings (matching the pattern) or Enum values; coerces to strings.
    """
    @field_validator("allowed", "disallowed", mode="before")
    @classmethod
    def coerce_enum_values(cls, v):  # type: ignore[override]
        # Normalize any Enum members to their string values
        if v is None:
            return []
        result = []
        for item in v:
            try:
                # Enum members have a 'value' attr; strings will just raise AttributeError
                result.append(getattr(item, "value", item))
            except Exception:
                result.append(item)
        return result

class ValueTypeCondition(AllowDisallowCondition[ValueType]):
    """
    Condition to gate by property value types using allow/disallow lists.
    """
    pass

class RegexCondition(ConstraintCondition):
    """Condition that specifies allowed values through regex pattern matching."""
    pattern: str  # The regex pattern to match against

class PromptCondition(ConstraintCondition):
    """Condition that uses a prompt for evaluation."""
    prompt: str  # The prompt to be used for this condition



class Constraint(BaseModel):
    """A constraint applied to a property based on various conditions.
    
    When used as a DAG edge payload, the property_id MUST match the source node's ID.
    This ensures constraints are properly bound to the upstream property they evaluate.

    If multiple conditions are assigned, the relationship between them will be OR.
    
    Attributes:
        conditions: List of constraint conditions to evaluate (OR relationship).
        target_status: Optional StatusCondition that determines when this constraint applies.
            - If specified: constraint is considered/applied only when the target node's status
              matches the allowed/disallowed status defined in the StatusCondition.
            - If None: constraint always applies regardless of target node status.
    """
    model_config = ConfigDict(extra='allow', frozen=True, populate_by_name=True)
    
    conditions: List[ConstraintCondition]

    target_status: Optional[StatusCondition] = None
    
    def to_dag_edge_name(self) -> str:
        """Return a string representation of this Constraint for DAG visualization.
        
        Returns:
            String label describing the constraint for DAG edge visualizations
        """
        # Build a descriptive label from active conditions
        labels = []
        for condition in self.conditions:
            if hasattr(condition, 'info') and hasattr(condition.info, 'name'):
                labels.append(condition.info.name)
        
        return " | ".join(labels) if labels else "constraint"
    
