"""Pydantic schemas for Canonical State Projector module.

This module contains all data models used by the Canonical State Projector interface.
"""

from enum import Enum
from typing import Annotated, Dict, List

from pydantic import Field

from ..base.schema import ProjectionContext, ProjectionResult
from ...state.canonical.schema import CanonicalState


class CanonicalProjectionStrategy(str, Enum):
    """Strategy for resolving multiple candidate values to canonical state."""

    HIGHEST_CONFIDENCE = "highest_confidence"
    THRESHOLD = "threshold"
    LLM_RESOLVE = "llm_resolve"
    MANUAL = "manual"
    CUSTOM = "custom"


class CanonicalProjectionContext(ProjectionContext):
    """Context provided to the canonical state projector for processing.

    Extends ProjectionContext with canonical projection-specific fields.
    """

    strategy: Annotated[
        CanonicalProjectionStrategy,
        Field(
            default=CanonicalProjectionStrategy.HIGHEST_CONFIDENCE,
            description="Resolution strategy to use",
        ),
    ]
    confidence_threshold: Annotated[
        float,
        Field(default=0.7, description="Minimum confidence for automatic resolution"),
    ]


class CanonicalProjectionResult(ProjectionResult):
    """Result of a canonical state projection operation."""

    updated_state: Annotated[
        CanonicalState,
        Field(
            description="The updated canonical state with resolved values (key: value format)"
        ),
    ]
    resolved_fields: Annotated[
        Dict[str, object],
        Field(
            default_factory=dict,
            description="Fields that were successfully resolved from interpretive state",
        ),
    ]
    pending_fields: Annotated[
        List[str],
        Field(
            default_factory=list,
            description="Fields that still need resolution (ambiguous/low confidence)",
        ),
    ]
    validation_errors: Annotated[
        Dict[str, str],
        Field(default_factory=dict, description="Any validation errors encountered"),
    ]
    requires_confirmation: Annotated[
        Dict[str, object],
        Field(
            default_factory=dict, description="Fields that require user confirmation"
        ),
    ]
    actions_triggered: Annotated[
        List[str],
        Field(
            default_factory=list,
            description="List of actions that were triggered based on validation",
        ),
    ]
