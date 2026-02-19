"""Projector module exports."""

from .base import (
    BaseProjector,
    ProjectionContext,
    ProjectionResult,
)
from .canonical import (
    BaseProjectorCanonicalState,
    CanonicalProjectionContext,
    CanonicalProjectionResult,
)
from .ui import (
    BaseProjectorUI,
    UIComponentType,
    UIComponent,
    UIProjectionContext,
    UIProjectionResult,
)

__all__ = [
    # Base
    "BaseProjector",
    "ProjectionContext",
    "ProjectionResult",
    # Canonical
    "BaseProjectorCanonicalState",
    "CanonicalProjectionContext",
    "CanonicalProjectionResult",
    # UI
    "BaseProjectorUI",
    "UIComponentType",
    "UIComponent",
    "UIProjectionContext",
    "UIProjectionResult",
]
