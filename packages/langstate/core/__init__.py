"""LangState Core module.

This module provides the base interfaces and implementations for LangState:
- Action: Execute business logic when state is complete
- Mutator: Process user input and update interpretive state
- Projector: Transform state to external representations (UI, Canonical)
- SchemaReader: Load and parse schema definitions
- State: Manage canonical and interpretive state
"""

from .action import (
    BaseAction,
    ActionStatus,
    ActionContext,
    ActionResult,
)
from .mutator import (
    BaseMutator,
    MutationContext,
    MutationResult,
)
from .projector import (
    BaseProjector,
    ProjectionContext,
    ProjectionResult,
    BaseProjectorCanonicalState,
    CanonicalProjectionStrategy,
    CanonicalProjectionContext,
    CanonicalProjectionResult,
    BaseProjectorUI,
    UIComponentType,
    UIComponent,
    UIProjectionContext,
    UIProjectionResult,
)
from .schema_reader import (
    BaseSchemaReader,
    Schema,
    SchemaField,
    SchemaReadResult,
)
from .state import (
    BaseState,
    Inference,
    ValueConfidence,
    FieldState,
    CanonicalState,
    CanonicalFieldState,
    CanonicalStateData,
    InterpretiveState,
    InterpretiveFieldState,
    InterpretiveStateData,
)

__all__ = [
    # Action
    "BaseAction",
    "ActionStatus",
    "ActionContext",
    "ActionResult",
    # Mutator
    "BaseMutator",
    "MutationContext",
    "MutationResult",
    # Projector - Base
    "BaseProjector",
    "ProjectionContext",
    "ProjectionResult",
    # Projector - Canonical
    "BaseProjectorCanonicalState",
    "CanonicalProjectionStrategy",
    "CanonicalProjectionContext",
    "CanonicalProjectionResult",
    # Projector - UI
    "BaseProjectorUI",
    "UIComponentType",
    "UIComponent",
    "UIProjectionContext",
    "UIProjectionResult",
    # Schema Reader
    "BaseSchemaReader",
    "Schema",
    "SchemaField",
    "SchemaReadResult",
    # State - Base
    "BaseState",
    "Inference",
    "ValueConfidence",
    "FieldState",
    # State - Canonical
    "CanonicalState",
    "CanonicalFieldState",
    "CanonicalStateData",
    # State - Interpretive
    "InterpretiveState",
    "InterpretiveFieldState",
    "InterpretiveStateData",
]
