"""Canonicalizer interface for LangState.

The Canonicalizer is responsible for:
- Receiving interpretive state with value-confidence pairs from Perceiver
- Validating field values and checking business rules/constraints
- Resolving interpretive state to canonical state (selecting best values)
- Triggering actions when validation passes
- Can be implemented as a conventional function or LLM-based
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field as PydField, ConfigDict

if TYPE_CHECKING:
    from ..models.field import State


class CanonicalizationStrategy(str, Enum):
    """Strategy for resolving multiple candidate values.

    Attributes:
        HIGHEST_CONFIDENCE: Select value with highest confidence score
        THRESHOLD: Select value only if confidence exceeds threshold
        LLM_RESOLVE: Use LLM to resolve ambiguous values
        MANUAL: Require manual user confirmation
        CUSTOM: Use custom resolution logic
    """

    HIGHEST_CONFIDENCE = "highest_confidence"
    THRESHOLD = "threshold"
    LLM_RESOLVE = "llm_resolve"
    MANUAL = "manual"
    CUSTOM = "custom"


class CanonicalizationResult(BaseModel):
    """Result of a canonicalization operation.

    Attributes:
        updated_state: The updated canonical state with resolved values (key: value format)
        resolved_fields: Fields that were successfully resolved from interpretive state
        pending_fields: Fields that still need resolution (ambiguous/low confidence)
        validation_errors: Any validation errors encountered
        requires_confirmation: Fields that require user confirmation
        actions_triggered: List of actions that were triggered based on validation
        metadata: Additional metadata about the canonicalization
    """

    updated_state: Any  # State - canonical state with resolved values
    resolved_fields: Dict[str, Any] = PydField(default_factory=dict)
    pending_fields: List[str] = PydField(default_factory=list)
    validation_errors: Dict[str, str] = PydField(default_factory=dict)
    requires_confirmation: Dict[str, Any] = PydField(default_factory=dict)
    actions_triggered: List[str] = PydField(default_factory=list)
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class CanonicalizationContext(BaseModel):
    """Context provided to the canonicalizer for processing.

    Attributes:
        interpretive_state: Current interpretive state with value-confidence pairs (key: [{value, confidence}])
        canonical_state: Current canonical state with resolved values (key: value)
        schema: The schema definition
        strategy: Resolution strategy to use
        confidence_threshold: Minimum confidence for automatic resolution
        metadata: Additional context metadata
    """

    interpretive_state: Any  # State - interpretive state with value-confidence pairs
    canonical_state: Optional[Any] = None  # State - canonical state with resolved values
    schema: Optional[Any] = None  # Schema
    strategy: CanonicalizationStrategy = CanonicalizationStrategy.HIGHEST_CONFIDENCE
    confidence_threshold: float = 0.7
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class BaseCanonicalizer(ABC):
    """Abstract base class for Canonicalizer implementations.

    The Canonicalizer receives the interpretive state (with value-confidence pairs)
    from the Perceiver, validates constraints, and produces the canonical state 
    (with resolved values). It can also trigger actions when validation passes.

    This can be implemented as:
    - A conventional function (rule-based, highest confidence, etc.)
    - An LLM-based resolver (for complex disambiguation)
    - A hybrid approach

    Example usage:
        class HighestConfidenceCanonicalizer(BaseCanonicalizer):
            async def canonicalize(
                self,
                context: CanonicalizationContext
            ) -> CanonicalizationResult:
                # Start with current canonical state or create new one
                new_canonical_state = context.canonical_state.copy() if context.canonical_state else State()
                resolved = {}
                pending = []
                actions = []

                # Iterate through interpretive state fields
                for node_id, node in context.interpretive_state.nodes.items():
                    field_instance = node.value
                    if not field_instance.snapshots:
                        pending.append(node_id)
                        continue

                    # Get the latest snapshot with value-confidence pairs
                    latest = field_instance.snapshots[-1]
                    if not latest.value_confidence_list:
                        pending.append(node_id)
                        continue

                    # Find value with highest confidence
                    top_value = max(
                        latest.value_confidence_list,
                        key=lambda x: x.score
                    )

                    if top_value.score >= context.confidence_threshold:
                        # Validate the value
                        is_valid, error = await self.validate_value(
                            node_id, top_value.value, context.schema
                        )
                        
                        if is_valid:
                            resolved[node_id] = top_value.value
                            # Update canonical state with resolved value
                            # Check if action should be triggered
                            if self._should_trigger_action(context, node_id):
                                actions.append(f"action_{node_id}")
                        else:
                            pending.append(node_id)
                    else:
                        pending.append(node_id)

                return CanonicalizationResult(
                    updated_state=new_canonical_state,
                    resolved_fields=resolved,
                    pending_fields=pending,
                    actions_triggered=actions
                )
    """

    @abstractmethod
    async def canonicalize(
        self, context: CanonicalizationContext
    ) -> CanonicalizationResult:
        """Resolve interpretive state to canonical state and validate.

        This method analyzes the interpretive state with value-confidence pairs,
        validates constraints, and produces a canonical state with resolved values.
        Can also trigger actions when validation passes.

        Args:
            context: CanonicalizationContext with interpretive state and current canonical state

        Returns:
            CanonicalizationResult with updated canonical state and any triggered actions
        """
        pass

    @abstractmethod
    async def validate_value(
        self, field_key: str, value: Any, schema: Optional[Any] = None
    ) -> tuple[bool, Optional[str]]:
        """Validate a single value against schema constraints.

        Args:
            field_key: The field key being validated
            value: The value to validate
            schema: Optional schema for validation rules

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    async def can_trigger_action(
        self, context: CanonicalizationContext
    ) -> tuple[bool, Optional[str]]:
        """Check if current state allows triggering an action.

        Args:
            context: CanonicalizationContext with current states

        Returns:
            Tuple of (can_trigger, action_name)
        """
        pass

    @abstractmethod
    async def initialize(self, schema: Any) -> None:
        """Initialize the canonicalizer with a schema.

        This method is called when the canonicalizer is first set up,
        allowing it to configure itself based on the schema definition.

        Args:
            schema: The schema definition to use for canonicalization
        """
        pass

    def get_strategy(self) -> CanonicalizationStrategy:
        """Get the current canonicalization strategy.

        Override this method to return the appropriate strategy.

        Returns:
            The canonicalization strategy being used
        """
        return CanonicalizationStrategy.HIGHEST_CONFIDENCE
