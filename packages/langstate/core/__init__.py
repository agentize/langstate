"""LangState Core module.

This module provides the base interfaces and implementations for LangState:
- Action: Execute business logic when state is complete
- Mutator: Process user input and update interpretive state
- Projector: Transform state to external representations (UI, Canonical)
- SpecExtractor: Load and parse schema definitions
- State: Manage canonical and interpretive state
- LangState: Main orchestrator coordinating all components
"""

from .state.base.base import BaseState
from .state.interpretive.schema import Inference, ValueConfidence
from .state.factory import BaseStateFactory, StateFactory
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
from .evaluator import (
    BaseEvaluator,
    Evaluator,
    EvaluationContext,
    EvaluationResult,
    FieldComparison,
    StateComparison,
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
from .spec_extractor import (
    BaseSpecExtractor,
    Schema,
    SchemaField,
)
from .state import (
    BaseCanonicalState,
    CanonicalStateSchema,
    BaseInterpretiveState,
    InterpretiveFieldState,
    InterpretiveStateSchema,
    BaseSnapshotStore,
)
from .langstate import (
    LangState,
    InputType,
    AgentInput,
    InteractionType,
    InteractionRequest,
    ActionResultData,
    LangStateConfig,
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
    # Evaluator
    "BaseEvaluator",
    "Evaluator",
    "EvaluationContext",
    "EvaluationResult",
    "FieldComparison",
    "StateComparison",
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
    # Spec Extractor
    "BaseSpecExtractor",
    "Schema",
    "SchemaField",
    # State - Base
    "BaseState",
    "Inference",
    "ValueConfidence",
    # State - Canonical
    "BaseCanonicalState",
    "CanonicalStateSchema",
    # State - Interpretive
    "BaseInterpretiveState",
    "InterpretiveFieldState",
    "InterpretiveStateSchema",
    "BaseSnapshotStore",
    # State - Factory
    "BaseStateFactory",
    "StateFactory",
    # LangState Orchestrator
    "LangState",
    "InputType",
    "AgentInput",
    "InteractionType",
    "InteractionRequest",
    "ActionResultData",
    "LangStateConfig",
]
