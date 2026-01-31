# LangState Core Architecture

## Overview

LangState uses a dual-state architecture to separate interpretive data (with inference and confidence) from canonical business state.

## Module Structure

```text
langstate/
├── core/
│   ├── action/
│   │   └── base/
│   │       ├── action.py       # BaseAction abstract class
│   │       └── schema.py       # ActionStatus, ActionContext, ActionResult
│   ├── mutator/
│   │   └── base/
│   │       ├── mutator.py      # BaseMutator abstract class
│   │       └── schema.py       # MutationContext, MutationResult
│   ├── projector/
│   │   ├── base/
│   │   │   ├── projector.py    # BaseProjector abstract class
│   │   │   └── schema.py       # ProjectionContext, ProjectionResult
│   │   ├── canonical/
│   │   │   ├── projector.py    # BaseProjectorCanonicalState
│   │   │   └── schema.py       # CanonicalProjectionContext, CanonicalProjectionResult
│   │   └── ui/
│   │       ├── projector.py    # BaseProjectorUI
│   │       └── schema.py       # UIComponent, UIProjectionContext, UIProjectionResult
│   ├── spec_extractor/
│   │   └── base/
│   │       ├── extractor.py    # BaseSpecExtractor abstract class
│   │       └── schema.py       # Schema, SchemaField
│   ├── state/
│   │   ├── base/
│   │   │   ├── state.py        # BaseState abstract class
│   │   │   └── schema.py       # Inference, ValueConfidence, FieldState
│   │   ├── canonical/
│   │   │   ├── state.py        # CanonicalState implementation
│   │   │   └── schema.py       # CanonicalFieldState, CanonicalStateData
│   │   └── interpretive/
│   │       ├── state.py        # InterpretiveState implementation
│   │       └── schema.py       # InterpretiveFieldState, InterpretiveStateData
│   └── langstate/
│       └── base/
│           ├── langstate.py    # LangState orchestrator abstract class
│           └── schema.py       # AgentInput, InteractionRequest, LangStateConfig
└── docs/
    └── ARCHITECTURE.md         # This file
```

### Design Principles

- **Separation of Concerns**: Each module has a `schema.py` for Pydantic data models and a main file for the abstract class
- **Explicit Types**: All Pydantic models use explicit types (no `Any`)
- **Inheritance**: Specialized projectors/states inherit from base classes

## LangState Orchestrator

The `LangState` class is the main entry point that coordinates all components:

### Key Responsibilities

- Initialize schema and components
- Manage canonical and interpretive states
- Orchestrate the conversation flow
- Invoke mutators, projectors, and actions

### Main Methods

- `initialize(config)`: Setup schema and initialize all components
- `invoke(agent_input)`: Process input and return next interaction or result
- `get_current_state()`: Access current interpretive state
- `get_canonical_state()`: Access current canonical state
- `reset()`: Reset state and restart conversation

### Component Management

- `set_spec_extractor()`: Configure spec extractor
- `set_mutator()`: Configure mutator
- `set_projector_canonical()`: Configure canonical projector
- `set_projector_ui()`: Replace all UI projectors
- `add_projector_ui()`: Add UI projector to the list
- `add_action_handler()`: Register action handlers

## State Types

### Canonical State

- **Format**: `{key: value}`
- **Purpose**: Business state for actions
- **Source**: Created from schema by `schema_to_init_state()`
- **Updated by**: ProjectorCanonicalState
- **Usage**: Final resolved values used for executing actions

### Interpretive State

- **Format**: `{key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}`
- **Purpose**: Track reasoning process and multiple value possibilities with confidence scores
- **Source**: Created from canonical state by `canonical_to_interpretive_state()`
- **Updated by**: Mutator
- **Usage**: Accumulates user inputs, inferences, and evolves through conversation

## Data Flow

```text
┌──────────┐
│  Schema  │
└────┬─────┘
     │ schema_to_init_state()
     ▼
┌──────────────────┐
│ Canonical State  │ {key: value}
│   (Initial)      │
└────┬─────────────┘
     │ canonical_to_interpretive_state()
     ▼
┌─────────────────────────────────────────────────────────┐
│ Interpretive State                                       │
│ {key: {inference: [{content, mutator_id}],              │
│        values: [{value, confidence}]}}                   │
└─────────────────────────────────────────────────────────┘
     │
     │ User Input (AgentInput)
     ▼
┌──────────────┐
│   Mutator    │ Updates interpretive state
└──────┬───────┘ Adds inferences and value-confidence pairs
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ Interpretive State (Updated)                             │
│ {key: {inference: [{content, mutator_id}],              │
│        values: [{value, confidence}]}}                   │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────┐
│ProjectorCanonical   │ Receives interpretive state
│State                │ Validates, can trigger actions
└──────┬──────────────┘ Updates canonical state
       │
       ▼
┌──────────────────┐
│ Canonical State  │ {key: value}
│   (Updated)      │
└──────┬───────────┘
       │
       ▼
┌─────────────────────┐
│ ProjectorsUI        │ Generates UI/prompts
│ (Multiple allowed)  │ All projectors are invoked
└─────────────────────┘
```

## Component Responsibilities

### SpecExtractors

- Read schema definitions (YAML, JSON, OpenAPI)
- Convert to internal Schema DAG
- Implementation: `OpenAPIYamlExtractor` in `langstate.state.readers`

### schema_to_init_state()

- Location: `langstate.state.core.schema_to_init_state`
- Converts Schema → Canonical State
- Creates {key: value} structure
- Applies default values from schema

### canonical_to_interpretive_state()

- Location: `langstate.state.core.schema_to_init_state`
- Converts Canonical State → Interpretive State
- Creates {key: {inference: [], values: [{value, confidence}]}} structure
- Wraps default values with confidence 0.0
- **Called only once** at initialization

### Mutator

- Receives user input (AgentInput: prompts, actions)
- Extracts field values from input
- **Updates interpretive state** by adding:
  - Inferences (reasoning steps with mutator_id)
  - Value-confidence pairs
- Returns updated interpretive state

### ProjectorCanonicalState

- **Receives interpretive state** as input
- Validates field values against constraints
- Resolves value-confidence pairs to single values
- **Checks if action can be triggered**
- **Can call action** when validation passes
- **Updates and returns canonical state**

### ProjectorsUI (Multiple Allowed)

- Generates UI components
- Creates natural language prompts
- Determines next fields to focus on
- Works with both states for context
- **Multiple projectors can be registered** to handle different UI interpretations
- All projectors are invoked and their results can be combined
- Use `set_projector_ui()` to replace all projectors
- Use `add_projector_ui()` to add projectors to the list

## Key Principles

1. **Separation of Concerns**
   - Interpretive state: Tracks uncertainty, reasoning, and evolution
   - Canonical state: Represents business logic and actions

2. **Single Responsibility**
   - Mutator: Only updates interpretive state
   - ProjectorCanonicalState: Validates and updates canonical state, triggers actions

3. **One-Way Flow**
   - User Input → Mutator → Interpretive State → ProjectorCanonicalState → Canonical State → ProjectorsUI
   - ProjectorCanonicalState receives interpretive state, not mutator output directly
   - Multiple UI projectors can be invoked in sequence

4. **Action Triggering**
   - Actions are triggered by ProjectorCanonicalState
   - Only when validation passes
   - Based on canonical state completeness

5. **Traceability**
   - Inferences track reasoning process with mutator_id
   - Enables explainability of how values were derived

## Example Implementation

```python
class MyLangState(LangState):
    def __init__(self):
        # Single UI projector
        super().__init__(
            spec_extractor=OpenAPIYamlExtractor(),
            mutator=MyCustomMutator(),
            projector_canonical=MyLLMProjectorCanonical(),
            projectors_ui=MyUIProjector()
        )

        # Or with multiple UI projectors
        super().__init__(
            spec_extractor=OpenAPIYamlExtractor(),
            mutator=MyCustomMutator(),
            projector_canonical=MyLLMProjectorCanonical(),
            projectors_ui=[MyUIProjector(), MyUIProjectorA()]
        )

    async def initialize(self, config: LangStateConfig) -> InteractionRequest:
        # 1. Load schema using configured extractor
        if self._spec_extractor and config.schema_source:
            self._schema = self._spec_extractor.read(config.schema_source)

        # 2. Create canonical state (key: value)
        self._canonical_state = schema_to_init_state(self._schema)

        # 3. Create interpretive state
        # Format: {key: {inference: [], values: [{value, confidence}]}}
        self._state = canonical_to_interpretive_state(self._canonical_state)

    async def invoke(
        self,
        agent_input: Optional[AgentInput] = None
    ) -> Union[InteractionRequest, ActionResult]:
        # 1. Mutator updates interpretive state
        mutation = await self.mutator.mutate(
            MutationContext(
                agent_input=agent_input,  # Structured input
                current_state=self._state,  # Interpretive state
                schema=self._schema
            )
        )
        self._state = mutation.updated_state  # Updated interpretive state

        # 2. ProjectorCanonicalState validates and updates canonical state
        projection = await self.projector_canonical.project(
            CanonicalProjectionContext(
                interpretive_state=self._state,  # Pass interpretive state
                canonical_state=self._canonical_state,
                schema=self._schema
            )
        )
        self._canonical_state = projection.updated_state  # Updated canonical state

        # 3. Check if actions were triggered
        if projection.actions_triggered:
            # Execute actions...
            pass

        # 4. ProjectorsUI generate UI (iterate over all projectors)
        ui_projections = []
        for projector in self._projectors_ui:
            ui_projection = await projector.project(
                UIProjectionContext(
                    interpretive_state=self._state,  # Interpretive state
                    canonical_state=self._canonical_state,  # Canonical state
                    schema=self._schema
                )
            )
            ui_projections.append(ui_projection)

        # 5. Check if complete
        if self._is_state_complete(self._canonical_state):
            return ActionResult(
                state=self._state,
                canonical_state=self._canonical_state
            )

        return await self._create_interaction_request()
```

## Interpretive State Structure

The interpretive state uses a rich structure to track both reasoning and values:

```python
{
    "field_key": {
        "inference": [
            {
                "content": "User said 'my name is John Doe'",
                "mutator_id": "llm_mutator_v1",
                "timestamp": "2026-01-18T10:30:00Z"
            }
        ],
        "values": [
            {"value": "John Doe", "confidence": 0.95},
            {"value": "John", "confidence": 0.60}
        ]
    }
}
```

This structure enables:

- **Traceability**: Know how each value was derived
- **Multi-value support**: Track multiple candidate values
- **Confidence scoring**: Rank values by confidence
- **Mutator attribution**: Track which component generated each inference

## AgentInput Structure

The `AgentInput` class provides structured input for agent invocation, supporting various interaction types:

```python
from langstate.core import AgentInput, InputType

class AgentInput(BaseModel):
    """Structured input for agent invocation."""

    input_type: InputType  # TEXT, ACTION, SELECTION, CONFIRMATION, FILE, SYSTEM
    text: Optional[str]  # Free-form text input
    action: Optional[str]  # Action identifier (button_id, form_name)
    action_data: Dict[str, object]  # Additional action parameters
    selection: List[object]  # Selected option(s)
    field_id: Optional[str]  # Target field for the input
    confirmed: Optional[bool]  # Confirmation status
    files: List[Dict[str, object]]  # File references
    metadata: Dict[str, object]  # Additional context

# Factory methods for common input types:
AgentInput.from_text("John Doe")
AgentInput.from_action("submit", {"form_id": "registration"})
AgentInput.from_selection(["option_1", "option_2"])
AgentInput.from_confirmation("email", confirmed=True)
```

## Usage Example

```python
from langstate.core import (
    LangState,
    LangStateConfig,
    AgentInput,
    BaseSpecExtractor,
    BaseMutator,
    BaseProjectorCanonicalState,
    BaseProjectorUI,
)

class MyLangState(LangState):
    async def initialize(self, config: LangStateConfig) -> None:
        # Load schema
        if self._spec_extractor and config.schema_source:
            self._schema = self._spec_extractor.read(config.schema_source)

        # Initialize components
        if self._mutator:
            await self._mutator.initialize(self._schema)
        if self._projector_canonical:
            await self._projector_canonical.initialize(self._schema)
        for projector in self._projectors_ui:
            await projector.initialize(self._schema)

        # Initialize states
        from langstate.core import CanonicalState, InterpretiveState
        self._canonical_state = CanonicalState()
        self._interpretive_state = InterpretiveState()

    async def invoke(self, agent_input=None, metadata=None):
        # Implementation of invoke logic
        pass

# Usage
langstate = MyLangState(
    spec_extractor=MySpecExtractor(),
    mutator=MyMutator(),
    projector_canonical=MyCanonicalProjector(),
    projectors_ui=[MyUIProjector()]
)

await langstate.initialize(LangStateConfig(schema_source="schema.yaml"))

# Initial invocation
interaction = await langstate.invoke()

# Process user input
result = await langstate.invoke(AgentInput.from_text("John Doe"))
```

## SpecExtractor Interface

The `BaseSpecExtractor` interface allows custom schema loading implementations:

```python
from langstate.core import BaseSpecExtractor, Schema

class BaseSpecExtractor(ABC):
    """Abstract base class for spec extractors."""

    @abstractmethod
    def read(self, source: Union[str, Path, Dict[str, object]]) -> Schema:
        """Read and parse schema from the given source."""
        pass

# Example implementations:
class OpenAPIYamlExtractor(BaseSpecExtractor):
    def read(self, source):
        # Load YAML and convert to Schema
        pass

class JSONSchemaExtractor(BaseSpecExtractor):
    def read(self, source):
        # Custom JSON schema loading
        pass
```
