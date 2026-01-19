"""Core module for LangState.

This module contains the core interfaces and abstractions for the LangState system:

- LangState: Main orchestrator class (agent-style interface)
- BaseSchemaReader: Interface for schema readers
- AgentInput: Structured input for agent invocation
- Mutator: Processes user input and updates interpretive state
- Projector: Base interface for state projection
  - ProjectorUI: Projects state to UI components and prompts
  - ProjectorCanonicalState: Projects interpretive state to canonical state
- Action: Executes business logic when state is complete

Models are imported from langstate.models package.
"""

from ..models.field import (
    State,
    FieldInstance,
    FieldSnapshot,
    ValueConfidence,
    Inference,
    Schema,
)
from ..models.ui import (
    UIComponent,
    UIComponentType,
)
from .mutator import (
    BaseMutator,
    MutationContext,
    MutationResult,
)
from .projector import (
    # Base projector
    BaseProjector,
    ProjectionContext,
    ProjectionResult,
    # UI Projector
    BaseProjectorUI,
    UIProjectionContext,
    UIProjectionResult,
    # Canonical State Projector
    BaseProjectorCanonicalState,
    CanonicalProjectionContext,
    CanonicalProjectionResult,
    CanonicalProjectionStrategy,
)
from .action import (
    BaseAction,
    ActionContext,
    ActionResult as ActionExecutionResult,
    ActionStatus,
)
from .langstate import (
    LangState,
    LangStateConfig,
    InteractionRequest,
    InteractionType,
    ActionResult,
    BaseSchemaReader,
    AgentInput,
    InputType,
)

__all__ = [
    # State models (from models package)
    "State",
    "FieldInstance",
    "FieldSnapshot",
    "ValueConfidence",
    "Inference",
    "Schema",
    # UI models (from models package)
    "UIComponent",
    "UIComponentType",
    # Mutator
    "BaseMutator",
    "MutationContext",
    "MutationResult",
    # Base Projector
    "BaseProjector",
    "ProjectionContext",
    "ProjectionResult",
    # UI Projector
    "BaseProjectorUI",
    "UIProjectionContext",
    "UIProjectionResult",
    # Canonical State Projector
    "BaseProjectorCanonicalState",
    "CanonicalProjectionContext",
    "CanonicalProjectionResult",
    "CanonicalProjectionStrategy",
    # Action
    "BaseAction",
    "ActionContext",
    "ActionExecutionResult",
    "ActionStatus",
    # Main class
    "LangState",
    "LangStateConfig",
    "InteractionRequest",
    "InteractionType",
    "ActionResult",
    # Schema Reader
    "BaseSchemaReader",
    # Agent Input
    "AgentInput",
    "InputType",
]
