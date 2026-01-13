from datetime import datetime
from pydantic import BaseModel, Field as PydField, ConfigDict, field_validator, model_validator
from typing import Any, Dict, List, Optional, Union, Generic, TypeVar, TYPE_CHECKING
from .basic import FieldStatus, Info, ValueType

T = TypeVar("T")
NumericType = TypeVar("NumericType", int, float, datetime)
    
class Range(Generic[NumericType], BaseModel):
    """Generic range type for numeric constraints.
    
    Represents a bounded numeric range with configurable inclusive/exclusive boundaries.
    Type-safe for either int or float types.
    
    Type Parameters:
        NumericType: Either int, float, or datetime
    
    Attributes:
        min: Minimum boundary value
        max: Maximum boundary value (must be >= min)
        inclusive_min: If True, values equal to min are allowed (default: True)
        inclusive_max: If True, values equal to max are allowed (default: True)
    
    Examples:
        >>> # Integer range: 18 to 65 (inclusive)
        >>> age_range = Range[int](min=18, max=65)
        
        >>> # Float range: 0.0 to 100.0 (exclusive upper bound)
        >>> percentage_range = Range[float](
        ...     min=0.0, max=100.0,
        ...     inclusive_min=True, inclusive_max=False
        ... )
    """
    min: NumericType
    max: NumericType
    inclusive_min: bool = True
    inclusive_max: bool = True
    
    @field_validator('max')
    @classmethod
    def validate_range(cls, v: NumericType, info) -> NumericType:
        """Ensure max >= min to maintain valid range invariant.
        
        Args:
            v: The max value being validated
            info: Validation context containing other field values
        
        Returns:
            NumericType: The validated max value
        
        Raises:
            ValueError: If max < min
        """
        if 'min' in info.data and v < info.data['min']:
            raise ValueError(f"max ({v}) must be greater than or equal to min ({info.data['min']})")
        return v

class Pattern(BaseModel):
    """Regular expression pattern wrapper for regex constraints.
    
    Encapsulates a regex pattern string with optional flags and metadata.
    
    Attributes:
        pattern: Regular expression pattern string
    
    Examples:
        >>> email_pattern = Pattern(pattern=r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$')
    """
    pattern: str

class Similarity(BaseModel):
    """Similarity matching configuration for value similarity constraints.
    
    Defines a reference value and similarity threshold for fuzzy matching.
    
    Attributes:
        reference: The reference value to compare against
        threshold: Similarity threshold (0.0 to 1.0)
    
    Examples:
        >>> sim = Similarity(reference="expected text", threshold=0.8)
    """
    reference: str
    threshold: float = PydField(ge=0.0, le=1.0)

class Prompt(BaseModel):
    """LLM prompt configuration for prompt-based constraints.
    
    Encapsulates a natural language prompt for LLM evaluation.
    
    Attributes:
        prompt: Natural language prompt describing validation criteria
    
    Examples:
        >>> p = Prompt(prompt="Check if the text is professional")
    """
    prompt: str

class ConstraintCondition(BaseModel):
    """Base class for all constraint conditions.
    
    A constraint condition represents a single evaluable condition that can be applied
    to a property value. This is an abstract base class that provides common structure
    for all specific condition types.
    
    All constraint conditions must have associated metadata (info) that describes
    the condition's purpose, name, and other contextual information.
    
    Attributes:
        info: Metadata information about this condition including name, description,
            display names for internationalization, URI reference, and custom metadata.
    
    See Also:
        - AllowDisallowCondition: Generic allow/disallow list filtering
        - RangeCondition: Numeric range validation
        - ValueSimilarityCondition: Similarity-based matching
        - StatusCondition: Field status filtering
        - ValueTypeCondition: Value type filtering
        - RegexCondition: Pattern matching validation
        - PromptCondition: LLM-based evaluation
    """
    info: Info

class AllowDisallowCondition(Generic[T], ConstraintCondition):
    """Generic class for allow/disallow list-based filtering logic.
    
    This condition implements a flexible filtering mechanism using allowlists and denylists.
    The evaluation follows a precedence-based policy to determine if a value is permitted.
    
    Evaluation Policy:
        1. If `allowed` is NON-EMPTY:
           - Only items explicitly listed in `allowed` are permitted
           - The `disallowed` list is completely ignored
           - This creates an "explicit allowlist" mode
        
        2. Else (if `allowed` is EMPTY):
           - All items are permitted by default
           - EXCEPT those explicitly listed in `disallowed`
           - This creates a "denylist" mode
        
        3. Both empty:
           - All items are permitted (no restrictions)
    
    Design Notes:
        - **Precedence**: Allowlist takes absolute precedence over denylist when non-empty
        - **Conflict Resolution**: If an item appears in both lists and `allowed` is non-empty,
          the item is ALLOWED (allowlist wins)
        - **Best Practice**: Don't mix both lists; use either allowlist OR denylist for clarity
        - **Omission Strategy**: When using allowlist mode, simply omit unwanted items rather
          than adding them to `disallowed`
    
    Type Parameters:
        T: The type of items being filtered (e.g., FieldStatus, ValueType, str)
    
    Attributes:
        allowed: List of explicitly permitted items. When non-empty, only these items pass.
        disallowed: List of explicitly forbidden items. Only used when `allowed` is empty.
        info: Inherited metadata about this condition
    
    Examples:
        >>> # Allowlist mode - only 'validated' and 'generated' are allowed
        >>> condition = AllowDisallowCondition(
        ...     allowed=['validated', 'generated'],
        ...     disallowed=['stale']  # This is ignored
        ... )
        >>> condition.matches('validated')  # True
        >>> condition.matches('stale')      # False (not in allowlist)
        
        >>> # Denylist mode - everything except 'stale' and 'unknown'
        >>> condition = AllowDisallowCondition(
        ...     allowed=[],
        ...     disallowed=['stale', 'unknown']
        ... )
        >>> condition.matches('validated')  # True
        >>> condition.matches('stale')      # False
        
        >>> # No restrictions - everything allowed
        >>> condition = AllowDisallowCondition(allowed=[], disallowed=[])
        >>> condition.matches('anything')   # True
    
    See Also:
        - StatusCondition: Specialized version for FieldStatus filtering
        - ValueTypeCondition: Specialized version for ValueType filtering
    """
    allowed: List[T] = PydField(default_factory=list)
    disallowed: List[T] = PydField(default_factory=list)

    def matches(self, value: T) -> bool:
        """Check if a given value matches the allow/disallow condition.
        
        Applies the evaluation policy to determine if the value passes the filter.
        
        Args:
            value: The value to evaluate against this condition
        
        Returns:
            bool: True if the value is permitted (matches the condition), False otherwise
        
        Examples:
            >>> condition = AllowDisallowCondition(allowed=['a', 'b'])
            >>> condition.matches('a')  # True
            >>> condition.matches('c')  # False
        """
        if self.allowed:
            return value in self.allowed
        return value not in self.disallowed

class RangeCondition(AllowDisallowCondition[Range]):
    """Numeric range validation condition using allow/disallow list logic.
    
    This condition validates that numeric values fall within specified ranges.
    It extends AllowDisallowCondition[Range] to support range-based filtering.
    
    The allowed/disallowed lists contain Range objects for complex range logic,
    while the class itself doesn't define range parameters directly.
    
    Attributes:
        allowed: List of allowed Range objects (optional)
        disallowed: List of disallowed Range objects (optional)
        info: Inherited metadata about this condition
    
    Examples:
        >>> # Single range: age must be between 18 and 65
        >>> condition = RangeCondition(
        ...     allowed=[Range(min=18.0, max=65.0)],
        ...     info=Info(name='valid_age_range')
        ... )
        
        >>> # Multiple ranges: valid percentage ranges
        >>> condition = RangeCondition(
        ...     allowed=[
        ...         Range(min=0.0, max=50.0),
        ...         Range(min=75.0, max=100.0)
        ...     ],
        ...     info=Info(name='percentage_ranges')
        ... )
    
    Notes:
        - Designed for numeric validation (int, float)
        - Each Range can have different inclusive/exclusive boundary settings
        - For discrete value sets, use AllowDisallowCondition[str] instead
        - For pattern-based validation, use RegexCondition instead
    
    See Also:
        - AllowDisallowCondition: Parent class defining the evaluation policy
        - Range: The generic range type
    """
    pass

class ValueSimilarityCondition(AllowDisallowCondition[Similarity]):
    """String similarity validation condition using allow/disallow list logic.
    
    This condition validates values based on similarity to reference values using
    similarity metrics (e.g., semantic similarity, edit distance). Extends
    AllowDisallowCondition[Similarity] for similarity-based filtering.
    
    The allowed/disallowed lists contain Similarity objects that define
    reference values and thresholds for fuzzy matching.
    
    Attributes:
        allowed: List of allowed Similarity configurations (optional)
        disallowed: List of disallowed Similarity configurations (optional)
        info: Inherited metadata about this condition
    
    Examples:
        >>> # Value must be at least 80% similar to reference text
        >>> condition = ValueSimilarityCondition(
        ...     allowed=[Similarity(reference="The quick brown fox", threshold=0.8)],
        ...     info=Info(name='text_similarity_check')
        ... )
        
        >>> # Multiple similarity thresholds
        >>> condition = ValueSimilarityCondition(
        ...     allowed=[
        ...         Similarity(reference="expected value 1", threshold=0.9),
        ...         Similarity(reference="expected value 2", threshold=0.85)
        ...     ],
        ...     info=Info(name='multi_reference_check')
        ... )
    
    Notes:
        - Similarity computation method is implementation-dependent
        - May use cosine similarity, Levenshtein distance, semantic embeddings, etc.
        - Threshold is validated to be in range [0.0, 1.0] via Pydantic constraints
        - For exact matching, consider using AllowDisallowCondition[str] instead
    
    See Also:
        - AllowDisallowCondition: Parent class defining the evaluation policy
        - Similarity: The similarity configuration type
    """
    pass

class StatusCondition(AllowDisallowCondition[FieldStatus]):
    """Field status filtering condition using allow/disallow list logic.
    
    This condition filters property values based on their status (e.g., untouched, 
    generated, edited, validated, stale). Inherits the allow/disallow evaluation 
    policy from AllowDisallowCondition.
    
    Type Safety:
        Specialized for FieldStatus type, which can be either:
        - FieldStatusEnum members (untouched, generated, edited, validated, stale, unknown, custom)
        - Custom status strings matching pattern ^[a-z_]+$
    
    Attributes:
        allowed: List of permitted field statuses (see AllowDisallowCondition for policy)
        disallowed: List of forbidden field statuses (see AllowDisallowCondition for policy)
        info: Inherited metadata about this condition
    
    Input Flexibility:
        Accepts values as either:
        - FieldStatusEnum enum members (e.g., FieldStatusEnum.VALIDATED)
        - String values (e.g., 'validated', 'generated')
        
        All inputs are automatically coerced to string values for consistent comparison.
    
    Examples:
        >>> # Only allow validated or generated statuses
        >>> condition = StatusCondition(
        ...     allowed=[FieldStatusEnum.VALIDATED, FieldStatusEnum.GENERATED],
        ...     info=Info(name='approved_statuses')
        ... )
        
        >>> # Exclude stale and unknown statuses (denylist mode)
        >>> condition = StatusCondition(
        ...     disallowed=['stale', 'unknown'],
        ...     info=Info(name='exclude_problematic')
        ... )
        
        >>> # Mix of enum and string inputs (both work)
        >>> condition = StatusCondition(
        ...     allowed=[FieldStatusEnum.EDITED, 'validated'],
        ...     info=Info(name='mixed_input_example')
        ... )
    
    See Also:
        - AllowDisallowCondition: Parent class defining the evaluation policy
        - FieldStatus: The type being filtered
        - FieldStatusEnum: Available predefined status values
    """
    @field_validator("allowed", "disallowed", mode="before")
    @classmethod
    def coerce_enum_values(cls, v):  # type: ignore[override]
        """Normalize enum members and strings to consistent string values.
        
        This validator ensures that both FieldStatusEnum members and string values
        can be used interchangeably in the allowed/disallowed lists.
        
        Args:
            v: Input list containing FieldStatusEnum members and/or strings
        
        Returns:
            List[str]: Normalized list of string values
        
        Examples:
            >>> # Input: [FieldStatusEnum.VALIDATED, 'generated']
            >>> # Output: ['validated', 'generated']
        """
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
    """Value type filtering condition using allow/disallow list logic.
    
    This condition filters property values based on their type (e.g., string, integer,
    number, boolean, array, reference). Inherits the allow/disallow evaluation policy
    from AllowDisallowCondition.
    
    Type Safety:
        Specialized for ValueType enum with values:
        - STRING: String values
        - INTEGER: Integer values
        - NUMBER: Numeric values (including floats)
        - BOOLEAN: Boolean values (True/False)
        - ARRAY: Array values (length managed, content in DAG)
        - REFERENCE: Reference values (ID string, content in DAG)
    
    Attributes:
        allowed: List of permitted value types (see AllowDisallowCondition for policy)
        disallowed: List of forbidden value types (see AllowDisallowCondition for policy)
        info: Inherited metadata about this condition
    
    Examples:
        >>> # Only allow primitive types
        >>> condition = ValueTypeCondition(
        ...     allowed=[ValueType.STRING, ValueType.INTEGER, ValueType.BOOLEAN],
        ...     info=Info(name='primitive_types_only')
        ... )
        
        >>> # Exclude complex types (denylist mode)
        >>> condition = ValueTypeCondition(
        ...     disallowed=[ValueType.ARRAY, ValueType.REFERENCE],
        ...     info=Info(name='no_complex_types')
        ... )
        
        >>> # Only allow numeric types
        >>> condition = ValueTypeCondition(
        ...     allowed=[ValueType.INTEGER, ValueType.NUMBER],
        ...     info=Info(name='numeric_only')
        ... )
    
    See Also:
        - AllowDisallowCondition: Parent class defining the evaluation policy
        - ValueType: The enum being filtered
    """
    pass

class RegexCondition(AllowDisallowCondition[Pattern]):
    """Pattern matching validation condition using allow/disallow list logic.
    
    This condition validates values using regular expression pattern matching.
    Extends AllowDisallowCondition[Pattern] for pattern-based filtering.
    
    The allowed/disallowed lists contain Pattern objects that define
    regex patterns for validation.
    
    Attributes:
        allowed: List of allowed Pattern objects (optional)
        disallowed: List of disallowed Pattern objects (optional)
        info: Inherited metadata about this condition
    
    Examples:
        >>> # Email address validation
        >>> condition = RegexCondition(
        ...     allowed=[Pattern(pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')],
        ...     info=Info(name='valid_email')
        ... )
        
        >>> # Multiple pattern options
        >>> condition = RegexCondition(
        ...     allowed=[
        ...         Pattern(pattern=r'^\d{3}-\d{3}-\d{4}$'),  # US phone
        ...         Pattern(pattern=r'^\d{10}$')              # Alternate format
        ...     ],
        ...     info=Info(name='phone_format')
        ... )
    
    Notes:
        - Pattern string should be a valid Python regular expression
        - Pattern matching implementation depends on the execution context
        - For exact value matching, use AllowDisallowCondition[str] instead
        - For numeric ranges, use RangeCondition instead
        - Consider performance implications for complex patterns on large datasets
    
    See Also:
        - AllowDisallowCondition: Parent class defining the evaluation policy
        - Pattern: The pattern configuration type
    """
    pass

class PromptCondition(AllowDisallowCondition[Prompt]):
    """LLM-based validation condition using allow/disallow list logic.
    
    This condition uses natural language prompts for LLM-based evaluation.
    Extends AllowDisallowCondition[Prompt] for prompt-based filtering.
    
    The allowed/disallowed lists contain Prompt objects that define
    natural language validation criteria for LLM evaluation.
    
    Attributes:
        allowed: List of allowed Prompt objects (optional)
        disallowed: List of disallowed Prompt objects (optional)
        info: Inherited metadata about this condition
    
    Examples:
        >>> # Semantic content validation
        >>> condition = PromptCondition(
        ...     allowed=[Prompt(prompt="Check if the text is professional and appropriate for business communication")],
        ...     info=Info(name='business_tone_check')
        ... )
        
        >>> # Multiple prompt criteria
        >>> condition = PromptCondition(
        ...     allowed=[
        ...         Prompt(prompt="Verify content is factually accurate"),
        ...         Prompt(prompt="Ensure tone is appropriate for audience")
        ...     ],
        ...     info=Info(name='content_quality')
        ... )
    
    Use Cases:
        - Semantic validation that requires understanding context
        - Quality assessment (tone, clarity, completeness)
        - Complex business rules that are hard to encode formally
        - Content moderation and appropriateness checking
        - Consistency checking across related fields
    
    Notes:
        - Evaluation requires LLM inference, which may have latency/cost implications
        - Prompt engineering is important for reliable, consistent results
        - Consider determinism requirements - LLM outputs may vary
        - For deterministic validation, prefer other condition types when possible
        - Ensure prompts are specific and unambiguous to minimize false positives/negatives
    
    See Also:
        - AllowDisallowCondition: Parent class defining the evaluation policy
        - Prompt: The prompt configuration type
    """
    pass



class Constraint(BaseModel):
    """A constraint applied to a property based on various conditions.
    
    Constraints define validation and dependency rules between properties in a state graph.
    They specify what values are acceptable for a property based on one or more evaluable
    conditions.
    
    DAG Integration:
        When used as a DAG (Directed Acyclic Graph) edge payload:
        - The edge source node represents the property being constrained (upstream dependency)
        - The edge target node represents the property that must satisfy the constraint
        - This creates a dependency: changes to source may invalidate target
        - Enables automatic validation and cascade updates through the property graph
    
    Condition Evaluation:
        Multiple conditions have an OR relationship:
        - If ANY condition is satisfied, the constraint passes
        - All conditions must fail for the constraint to fail
        - Empty conditions list means constraint always passes
    
    Conditional Application (target_status):
        Constraints can be conditionally applied based on the target property's status:
        - If target_status is specified: constraint only applies when the target node's
          current status matches the allowed/disallowed statuses in the StatusCondition
        - If target_status is None: constraint always applies regardless of target status
        - This enables status-dependent validation (e.g., only validate when 'edited')
    
    Model Configuration:
        - extra='allow': Permits additional fields for extensibility
        - frozen=True: Constraints are immutable after creation
        - populate_by_name=True: Supports field aliases during construction
    
    Attributes:
        conditions: List of ConstraintCondition objects to evaluate (OR relationship).
            Each condition represents a different validation rule.
        target_status: Optional StatusCondition that gates when this constraint applies.
            - If specified: only apply constraint when target node status matches
            - If None: always apply constraint
    
    Examples:
        >>> # Simple constraint: value must be in enumeration
        >>> constraint = Constraint(
        ...     conditions=[
        ...         AllowDisallowCondition(allowed=['red', 'green', 'blue'], info=Info(name='colors'))
        ...     ]
        ... )
        
        >>> # Multiple conditions (OR): value must be in range OR match pattern
        >>> constraint = Constraint(
        ...     conditions=[
        ...         RangeCondition(min=0, max=100, info=Info(name='percentage')),
        ...         RegexCondition(pattern=r'^N/A$', info=Info(name='not_applicable'))
        ...     ]
        ... )
        
        >>> # Conditional constraint: only apply when target is 'edited'
        >>> constraint = Constraint(
        ...     conditions=[
        ...         AllowDisallowCondition(allowed=['active', 'inactive'], info=Info(name='status'))
        ...     ],
        ...     target_status=StatusCondition(
        ...         allowed=[FieldStatusEnum.EDITED],
        ...         info=Info(name='only_when_edited')
        ...     )
        ... )
    
    See Also:
        - ConstraintCondition: Base class for all condition types
        - DAG edge usage: Constraints as edge payloads in property dependency graphs
    """
    model_config = ConfigDict(extra='allow', frozen=True, populate_by_name=True)
    
    conditions: List[ConstraintCondition]

    target_status: Optional[StatusCondition] = None
    
    def to_dag_edge_name(self) -> str:
        """Return a string representation of this Constraint for DAG visualization.
        
        Generates a human-readable label summarizing the constraint's conditions,
        suitable for displaying on DAG edges in graph visualizations.
        
        Returns:
            str: Pipe-separated (|) list of condition names, or "constraint" if no names available
        
        Examples:
            >>> # Constraint with named conditions
            >>> constraint = Constraint(conditions=[
            ...     AllowDisallowCondition(allowed=[1,2,3], info=Info(name='valid_ids')),
            ...     RangeCondition(min=0, max=10, info=Info(name='range_check'))
            ... ])
            >>> constraint.to_dag_edge_name()
            'valid_ids | range_check'
            
            >>> # Constraint without named conditions
            >>> constraint = Constraint(conditions=[
            ...     AllowDisallowCondition(allowed=[1,2,3], info=Info())
            ... ])
            >>> constraint.to_dag_edge_name()
            'constraint'
        """
        # Build a descriptive label from active conditions
        labels = []
        for condition in self.conditions:
            if hasattr(condition, 'info') and hasattr(condition.info, 'name'):
                labels.append(condition.info.name)
        
        return " | ".join(labels) if labels else "constraint"
    
