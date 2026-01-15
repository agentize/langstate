"""Core module for LangState.

This module contains the core interfaces and abstractions for the LangState system:

- LangState: Main orchestrator class
- Perceiver: Processes user input and updates interpretive state
- Canonicalizer: Converts interpretive state to canonical state
- Interpreter: Generates UI components and LLM completions
- Action: Executes business logic when state is complete
- States: Interpretive and Canonical state representations
- SchemaReader: Reads and parses schema definitions
"""

from .states import (
    InterpretiveState,
    CanonicalState,
    ValueWithConfidence,
)
from .perceiver import BasePerceiver, PerceptionContext, PerceptionResult
from .canonicalizer import (
    BaseCanonicalizer,
    CanonicalizationContext,
    CanonicalizationResult,
    CanonicalizationStrategy,
)
from .interpreter import (
    BaseInterpreter,
    InterpretationContext,
    InterpretationResult,
    UIComponent,
    UIComponentType,
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
)

__all__ = [
    # States
    "InterpretiveState",
    "CanonicalState",
    "ValueWithConfidence",
    # Perceiver
    "BasePerceiver",
    "PerceptionContext",
    "PerceptionResult",
    # Canonicalizer
    "BaseCanonicalizer",
    "CanonicalizationContext",
    "CanonicalizationResult",
    "CanonicalizationStrategy",
    # Interpreter
    "BaseInterpreter",
    "InterpretationContext",
    "InterpretationResult",
    "UIComponent",
    "UIComponentType",
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
]
