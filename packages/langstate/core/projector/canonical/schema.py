"""Pydantic schemas for Canonical State Projector module.

This module contains all data models used by the Canonical State Projector interface.
"""

from enum import Enum
from typing import Dict, List

from pydantic import Field

from ..base.schema import ProjectionContext, ProjectionResult


class CanonicalProjectionStrategy(str, Enum):
    """Strategy for resolving multiple candidate values to canonical state.

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


class CanonicalProjectionContext(ProjectionContext):
    """Context provided to the canonical state projector for processing.

    Extends ProjectionContext with canonical projection-specific fields.

    Attributes:
        strategy: Resolution strategy to use
        confidence_threshold: Minimum confidence for automatic resolution
    """

    strategy: CanonicalProjectionStrategy = (
        CanonicalProjectionStrategy.HIGHEST_CONFIDENCE
    )
    confidence_threshold: float = 0.7


class CanonicalProjectionResult(ProjectionResult):
    """Result of a canonical state projection operation.

    Attributes:
        updated_state: The updated canonical state with resolved values (key: value format)
        resolved_fields: Fields that were successfully resolved from interpretive state
        pending_fields: Fields that still need resolution (ambiguous/low confidence)
        validation_errors: Any validation errors encountered
        requires_confirmation: Fields that require user confirmation
        actions_triggered: List of actions that were triggered based on validation
    """

    updated_state: Dict[str, object] = Field(default_factory=dict)
    resolved_fields: Dict[str, object] = Field(default_factory=dict)
    pending_fields: List[str] = Field(default_factory=list)
    validation_errors: Dict[str, str] = Field(default_factory=dict)
    requires_confirmation: Dict[str, object] = Field(default_factory=dict)
    actions_triggered: List[str] = Field(default_factory=list)
