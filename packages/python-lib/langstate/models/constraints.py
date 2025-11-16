from pydantic import BaseModel, Field as PydField, ConfigDict, field_validator, model_validator
from typing import Any, Dict, List, Optional, Union, Generic, TypeVar, TYPE_CHECKING
try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias
from datetime import datetime, timezone
from .basic import FieldStatus, Info, ValueType

T = TypeVar("T")

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
        - EnumerationCondition: Exact value enumeration matching
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

class RangeCondition(ConstraintCondition):
    """Condition that validates numeric values within a specified range.
    
    This condition checks if a numeric value falls within defined minimum and maximum
    bounds, with configurable inclusive/exclusive boundary behavior.
    
    Attributes:
        min: Minimum boundary value for the range
        max: Maximum boundary value for the range (must be >= min)
        inclusive_min: If True, values equal to min are allowed (default: True)
        inclusive_max: If True, values equal to max are allowed (default: True)
        info: Inherited metadata about this condition
    
    Examples:
        >>> # Age must be between 18 and 65 (inclusive)
        >>> condition = RangeCondition(
        ...     min=18.0, max=65.0,
        ...     inclusive_min=True, inclusive_max=True,
        ...     info=Info(name='valid_age_range')
        ... )
        
        >>> # Temperature between 0 and 100 (exclusive upper bound)
        >>> condition = RangeCondition(
        ...     min=0.0, max=100.0,
        ...     inclusive_min=True, inclusive_max=False,
        ...     info=Info(name='temperature_range')
        ... )
    
    Validation:
        - Automatically validates that max >= min during model construction
        - Raises ValueError if max < min
    
    Notes:
        - Designed for numeric validation (int, float)
        - For discrete value sets, use EnumerationCondition instead
        - For pattern-based validation, use RegexCondition instead
    """
    min: float
    max: float
    inclusive_min: bool = True
    inclusive_max: bool = True
    
    @field_validator('max')
    @classmethod
    def validate_range(cls, v: float, info) -> float:
        """Ensure max >= min to maintain valid range invariant.
        
        Args:
            v: The max value being validated
            info: Validation context containing other field values
        
        Returns:
            float: The validated max value
        
        Raises:
            ValueError: If max < min
        """
        if 'min' in info.data and v < info.data['min']:
            raise ValueError(f"max ({v}) must be greater than or equal to min ({info.data['min']})")
        return v

class ValueSimilarityCondition(ConstraintCondition):
    """Condition that validates values based on similarity to a reference value.
    
    This condition uses similarity metrics (e.g., semantic similarity, edit distance)
    to determine if a value is sufficiently similar to a reference value. Useful for
    fuzzy matching, near-duplicate detection, or semantic validation.
    
    Attributes:
        reference: The reference value to compare against
        threshold: Similarity threshold (0.0 to 1.0) where:
            - 0.0 = no similarity required (accepts anything)
            - 1.0 = exact match required
            - Values in between define acceptable similarity levels
        info: Inherited metadata about this condition
    
    Examples:
        >>> # Value must be at least 80% similar to reference text
        >>> condition = ValueSimilarityCondition(
        ...     reference="The quick brown fox",
        ...     threshold=0.8,
        ...     info=Info(name='text_similarity_check')
        ... )
        
        >>> # Exact match required (100% similarity)
        >>> condition = ValueSimilarityCondition(
        ...     reference="expected_value",
        ...     threshold=1.0,
        ...     info=Info(name='exact_match')
        ... )
    
    Notes:
        - Similarity computation method is implementation-dependent
        - May use cosine similarity, Levenshtein distance, semantic embeddings, etc.
        - Threshold is validated to be in range [0.0, 1.0] via Pydantic constraints
        - For exact matching, consider using EnumerationCondition instead
    """
    reference: str
    threshold: float = PydField(ge=0.0, le=1.0)  # Similarity threshold (0-1.0)

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

class RegexCondition(ConstraintCondition):
    """Condition that validates values using regular expression pattern matching.
    
    This condition checks if a value matches a specified regex pattern, enabling
    flexible string validation based on format, structure, or content patterns.
    
    Attributes:
        pattern: Regular expression pattern string to match against property values
        info: Inherited metadata about this condition
    
    Examples:
        >>> # Email address validation
        >>> condition = RegexCondition(
        ...     pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        ...     info=Info(name='valid_email')
        ... )
        
        >>> # UUID format validation
        >>> condition = RegexCondition(
        ...     pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        ...     info=Info(name='uuid_format')
        ... )
        
        >>> # Phone number format (US)
        >>> condition = RegexCondition(
        ...     pattern=r'^\d{3}-\d{3}-\d{4}$',
        ...     info=Info(name='us_phone_format')
        ... )
    
    Notes:
        - Pattern string should be a valid Python regular expression
        - Pattern matching implementation depends on the execution context
        - For exact value matching, use EnumerationCondition instead
        - For numeric ranges, use RangeCondition instead
        - Consider performance implications for complex patterns on large datasets
    """
    pattern: str  # The regex pattern to match against

class PromptCondition(ConstraintCondition):
    """Condition that uses a natural language prompt for LLM-based evaluation.
    
    This condition leverages Language Model evaluation to determine if a property
    value satisfies complex, semantic, or context-dependent criteria that may be
    difficult to express through rigid rules.
    
    Attributes:
        prompt: Natural language prompt describing the validation criteria.
            The prompt should clearly specify what constitutes a valid/invalid value.
        info: Inherited metadata about this condition
    
    Examples:
        >>> # Semantic content validation
        >>> condition = PromptCondition(
        ...     prompt="Check if the text is professional and appropriate for business communication",
        ...     info=Info(name='business_tone_check')
        ... )
        
        >>> # Context-aware validation
        >>> condition = PromptCondition(
        ...     prompt="Verify that the description accurately reflects the product category and includes required safety information",
        ...     info=Info(name='product_description_completeness')
        ... )
        
        >>> # Quality assessment
        >>> condition = PromptCondition(
        ...     prompt="Evaluate if the code comment clearly explains the algorithm's purpose and complexity",
        ...     info=Info(name='comment_quality')
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
    """
    prompt: str  # The prompt to be used for this condition



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
        ...         EnumerationCondition(values=['red', 'green', 'blue'], info=Info(name='colors'))
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
        ...         EnumerationCondition(values=['active', 'inactive'], info=Info(name='status'))
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
            ...     EnumerationCondition(values=[1,2,3], info=Info(name='valid_ids')),
            ...     RangeCondition(min=0, max=10, info=Info(name='range_check'))
            ... ])
            >>> constraint.to_dag_edge_name()
            'valid_ids | range_check'
            
            >>> # Constraint without named conditions
            >>> constraint = Constraint(conditions=[
            ...     EnumerationCondition(values=[1,2,3], info=Info())
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
    
