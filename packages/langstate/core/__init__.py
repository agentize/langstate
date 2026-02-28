"""LangState Core module.

This module provides the base interfaces and implementations for LangState:
- Action: Execute business logic when state is complete
- Mutator: Process user input and update state
- Projector: Transform state to external representations (UI)
- SpecExtractor: Load and parse schema definitions
- State: Manage structured state
- LangState: Main orchestrator coordinating all components
"""

from .state import BaseDAHState, DAHState
from .state.state.schema import (
    Inference,
    ValueConfidence,
    InterpretiveField,
    StateSchema,
)
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
    StructuredInput,
    LLMMutator,
    BaseLLMClient,
)
from .evaluator import (
    BaseEvaluator,
    Evaluator,
    LLMEvaluator,
    EvaluationContext,
    EvaluationResult,
    FieldComparison,
    StateComparison,
)
from .projector import (
    BaseProjector,
    ProjectionContext,
    ProjectionResult,
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
    SourceType,
)
from .state import (
    BaseState,
    State,
    Snapshot,
    BaseRepository,
    BaseSnapshotRepository,
    HistoryFilter,
    InMemorySnapshotRepository,
    BaseStateTransformer,
)
from .langstate import (
    BaseLangState,
    LangState,
    LangStateDeps,
    InputType,
    AgentInput,
    InteractionType,
    InteractionRequest,
    StateResultData,
    LangStateConfig,
    schema_to_state,
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
    "StructuredInput",
    "LLMMutator",
    "BaseLLMClient",
    # Evaluator
    "BaseEvaluator",
    "Evaluator",
    "LLMEvaluator",
    "EvaluationContext",
    "EvaluationResult",
    "FieldComparison",
    "StateComparison",
    # Projector - Base
    "BaseProjector",
    "ProjectionContext",
    "ProjectionResult",
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
    "SourceType",
    # State - Base
    "BaseDAHState",
    "DAHState",
    "BaseState",
    "State",
    "StateSchema",
    "InterpretiveField",
    "Inference",
    "ValueConfidence",
    # State - Snapshot
    "Snapshot",
    # State - Repository
    "BaseRepository",
    "BaseSnapshotRepository",
    "HistoryFilter",
    "InMemorySnapshotRepository",
    # State - Transformer
    "BaseStateTransformer",
    # LangState Orchestrator
    "BaseLangState",
    "LangState",
    "LangStateDeps",
    "InputType",
    "AgentInput",
    "InteractionType",
    "InteractionRequest",
    "StateResultData",
    "LangStateConfig",
    "schema_to_state",
]
