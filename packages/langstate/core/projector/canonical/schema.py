"""Pydantic schemas for Canonical State Projector module.

This module contains all data models used by the Canonical State Projector interface.
"""

from typing import Annotated, Dict, List

from pydantic import Field

from core.state.state.base import BaseState

from ..base.schema import ProjectionContext, ProjectionResult


class CanonicalProjectionContext(ProjectionContext):
    """Context provided to the canonical state projector for processing.

    Extends ProjectionContext with canonical projection-specific fields.
    """

    confidence_threshold: Annotated[
        float,
        Field(default=0.7, description="Minimum confidence for automatic resolution"),
    ]


class CanonicalProjectionResult(ProjectionResult):
    """Result of a canonical state projection operation."""

    updated_state: Annotated[
        BaseState,
        Field(
            description="The updated canonical state with resolved values (key: value format)"
        ),
    ]
    resolved_fields: Annotated[
        Dict[str, object],
        Field(
            default_factory=dict,
            description="Fields that were successfully resolved from current state",
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
