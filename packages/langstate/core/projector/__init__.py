"""Projector module exports."""

from .base import (
    BaseProjector,
    ProjectionContext,
    ProjectionResult,
)
from .canonical import (
    BaseProjectorCanonicalState,
    CanonicalProjectionStrategy,
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
    "CanonicalProjectionStrategy",
    "CanonicalProjectionContext",
    "CanonicalProjectionResult",
    # UI
    "BaseProjectorUI",
    "UIComponentType",
    "UIComponent",
    "UIProjectionContext",
    "UIProjectionResult",
]
