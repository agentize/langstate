"""Canonicalizer interface for LangState.

The Canonicalizer is responsible for:
- Resolving field values from multiple snapshots with different confidences
- Applying business rules and validation
- Managing constraint satisfaction in the state graph
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
        updated_state: The updated state graph with resolved values
        resolved_fields: Fields that were successfully resolved
        pending_fields: Fields that still need resolution (ambiguous/low confidence)
        validation_errors: Any validation errors encountered
        requires_confirmation: Fields that require user confirmation
        metadata: Additional metadata about the canonicalization
    """

    updated_state: Any  # State
    resolved_fields: Dict[str, Any] = PydField(default_factory=dict)
    pending_fields: List[str] = PydField(default_factory=list)
    validation_errors: Dict[str, str] = PydField(default_factory=dict)
    requires_confirmation: Dict[str, Any] = PydField(default_factory=dict)
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class CanonicalizationContext(BaseModel):
    """Context provided to the canonicalizer for processing.

    Attributes:
        current_state: Current state graph with field snapshots
        schema: The schema definition
        strategy: Resolution strategy to use
        confidence_threshold: Minimum confidence for automatic resolution
        metadata: Additional context metadata
    """

    current_state: Any  # State
    schema: Optional[Any] = None  # Schema
    strategy: CanonicalizationStrategy = CanonicalizationStrategy.HIGHEST_CONFIDENCE
    confidence_threshold: float = 0.7
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class BaseCanonicalizer(ABC):
    """Abstract base class for Canonicalizer implementations.

    The Canonicalizer resolves field values from multiple snapshots with different
    confidence scores. It selects the most appropriate value for each field based
    on the strategy and constraints defined in the schema.

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
                new_state = context.current_state.copy()
                resolved = {}
                pending = []

                # Iterate through all field instances
                for node_id, node in new_state.nodes.items():
                    field_instance = node.value
                    if not field_instance.snapshots:
                        pending.append(node_id)
                        continue

                    # Get the latest snapshot
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
                        resolved[node_id] = top_value.value
                    else:
                        pending.append(node_id)

                return CanonicalizationResult(
                    updated_state=new_state,
                    resolved_fields=resolved,
                    pending_fields=pending
                )
    """

    @abstractmethod
    async def canonicalize(
        self, context: CanonicalizationContext
    ) -> CanonicalizationResult:
        """Resolve field values from snapshots in the state graph.

        This method analyzes field snapshots with multiple candidate values
        and resolves them based on confidence scores and constraints.

        Args:
            context: CanonicalizationContext containing state and configuration

        Returns:
            CanonicalizationResult with the updated state graph
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
