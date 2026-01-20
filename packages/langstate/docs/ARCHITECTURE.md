# LangState Core Architecture

## Overview

LangState uses a dual-state architecture to separate interpretive data (with inference and confidence) from canonical business state.

## Module Structure

```
langstate/
├── core/                    # Interfaces and orchestrator
│   ├── action.py           # BaseAction interface
│   ├── langstate.py        # LangState orchestrator, BaseSchemaReader
│   ├── mutator.py          # BaseMutator interface
│   └── projector.py        # BaseProjector, ProjectorUI (supports multiple), ProjectorCanonicalState
├── models/                  # Data models (Pydantic)
│   ├── basic.py            # Basic types (FieldStatus, ValueType, etc.)
│   ├── constraints.py      # Constraint models
│   ├── field.py            # Field, FieldInstance, Schema, State
│   └── ui.py               # UIComponent, UIComponentType
├── state/                   # State management and readers
│   ├── core/
│   │   └── schema_to_init_state.py  # schema_to_init_state, canonical_to_interpretive_state
│   └── readers/
│       └── yaml.py         # OpenAPIYamlReader implementation
└── data_structure/          # Graph structures (DAG, DAH)
```

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

```
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

### SchemaReaders

- Read schema definitions (YAML, JSON, OpenAPI)
- Convert to internal Schema DAG
- Implementation: `OpenAPIYamlReader` in `langstate.state.readers`

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
            schema_reader=OpenAPIYamlReader(),
            mutator=MyCustomMutator(),
            projector_canonical=MyLLMProjectorCanonical(),
            projectors_ui=MyUIProjector()
        )
        
        # Or with multiple UI projectors
        super().__init__(
            schema_reader=OpenAPIYamlReader(),
            mutator=MyCustomMutator(),
            projector_canonical=MyLLMProjectorCanonical(),
            projectors_ui=[MyUIProjector(), MyUIProjectorA()]
        )

    async def initialize(self, config: LangStateConfig) -> InteractionRequest:
        # 1. Load schema using configured reader
        if self._schema_reader and config.schema_source:
            self._schema = self._schema_reader.read(config.schema_source)

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
class AgentInput(BaseModel):
    """Structured input for agent invocation."""

    input_type: InputType  # TEXT, ACTION, SELECTION, CONFIRMATION, FILE, SYSTEM
    text: Optional[str]  # Free-form text input
    action: Optional[str]  # Action identifier (button_id, form_name)
    action_data: Dict[str, Any]  # Additional action parameters
    selection: List[Any]  # Selected option(s)
    field_id: Optional[str]  # Target field for the input
    confirmed: Optional[bool]  # Confirmation status
    files: List[Dict[str, Any]]  # File references
    metadata: Dict[str, Any]  # Additional context

# Factory methods for common input types:
AgentInput.from_text("John Doe")
AgentInput.from_action("submit", {"form_id": "registration"})
AgentInput.from_selection(["option_1", "option_2"])
AgentInput.from_confirmation("email", confirmed=True)
```

## SchemaReader Interface

The `BaseSchemaReader` interface allows custom schema loading implementations:

```python
class BaseSchemaReader(ABC):
    """Abstract base class for schema readers."""

    @abstractmethod
    def read(self, source: Union[str, Path, Dict[str, Any]]) -> Schema:
        """Read and parse schema from the given source."""
        pass

# Example implementations:
class OpenAPIYamlReader(BaseSchemaReader):
    def read(self, source):
        from langstate.state.readers.yaml import load_schema_from_openapi_yaml
        return load_schema_from_openapi_yaml(source)

class JSONSchemaReader(BaseSchemaReader):
    def read(self, source):
        # Custom JSON schema loading
        pass
```
