"""Core module for LangState.

This module contains the core interfaces and abstractions for the LangState system:

- LangState: Main orchestrator class (agent-style interface)
- BaseSchemaReader: Interface for schema readers
- AgentInput: Structured input for agent invocation
- Perceiver: Processes user input and updates state
- Canonicalizer: Resolves state values with constraints
- Interpreter: Generates UI components and LLM completions
- Action: Executes business logic when state is complete
- State: Graph-based state representation with Field instances
"""

from ..models.field import (
    State,
    FieldInstance,
    FieldSnapshot,
    ValueConfidence,
    Schema,
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
    BaseSchemaReader,
    AgentInput,
    InputType,
)

__all__ = [
    # State - Graph-based representation
    "State",
    "FieldInstance",
    "FieldSnapshot",
    "ValueConfidence",
    "Schema",
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
    # Schema Reader
    "BaseSchemaReader",
    # Agent Input
    "AgentInput",
    "InputType",
]
