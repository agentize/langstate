# LangState Core - Quick Reference

## Key Changes

### Two State Types

1. **Canonical State** - `{key: value}` - Business state for actions
2. **Interpretive State** - `{key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}` - Tracks reasoning and uncertainty

### Agent-Style Interface

LangState follows agent SDK conventions (similar to OpenAI Agents SDK):

- Main method is `invoke()` instead of `process_input()`
- Input is structured via `AgentInput` to support various interaction types
- Schema readers implement `BaseSchemaReader` interface

### New Flow

```
Schema → Canonical State → Interpretive State → [User Loop]
                                  ↓
                            Mutator (updates interpretive with inferences + values)
                                  ↓
                            ProjectorCanonicalState (validates, triggers actions, updates canonical)
                                  ↓
                            ProjectorUI (generates UI)
```

### Component Updates

- **BaseMutator**: Updates interpretive state with inferences and value-confidence pairs
- **BaseProjectorCanonicalState**: Receives interpretive state, validates, can trigger actions, returns canonical state
- **BaseProjectorUI**: Generates UI components and prompts
- **BaseSchemaReader**: Interface for schema loading (e.g., `OpenAPIYamlReader`)
- **schema_to_init_state()**: Creates canonical state (not interpretive)
- **canonical_to_interpretive_state()**: Converts canonical → interpretive (called once at init)

### Usage Example

```python
from langstate import (
    LangState, LangStateConfig, AgentInput,
    BaseSchemaReader, OpenAPIYamlReader,
    BaseMutator, BaseProjectorCanonicalState, BaseProjectorUI
)

# Create LangState with components
langstate = MyLangState(
    schema_reader=OpenAPIYamlReader(),
    mutator=MyCustomMutator(),
    projector_canonical=MyLLMProjectorCanonical(),
    projector_ui=MyUIProjector()
)

# Or use setters
langstate = MyLangState()
langstate.set_schema_reader(OpenAPIYamlReader())
langstate.set_mutator(MyCustomMutator())
langstate.set_projector_canonical(MyLLMProjectorCanonical())
langstate.set_projector_ui(MyUIProjector())

# Initialize
await langstate.initialize(LangStateConfig(schema_source="./schema.yaml"))

# Get first interaction
interaction = await langstate.invoke()

# Process text input
result = await langstate.invoke(AgentInput.from_text("John Doe"))

# Process button click
result = await langstate.invoke(AgentInput.from_action("submit", {"form_id": "reg"}))

# Process selection
result = await langstate.invoke(AgentInput.from_selection(["option_1"]))

# Process confirmation
result = await langstate.invoke(AgentInput.from_confirmation("email", confirmed=True))
```

### AgentInput Types

```python
# Text input
AgentInput.from_text("John Doe")

# Action (button click, form submit)
AgentInput.from_action("submit", {"form_id": "registration"})

# Selection from options
AgentInput.from_selection(["option_1", "option_2"])

# Confirmation
AgentInput.from_confirmation("email", confirmed=True)

# Full structured input
AgentInput(
    input_type=InputType.ACTION,
    action="submit_form",
    action_data={"form_id": "registration"},
    metadata={"source": "mobile_app"}
)
```

### Interpretive State Structure

```python
{
    "field_key": {
        "inference": [
            {"content": "User said 'my name is John'", "mutator_id": "llm_mutator"}
        ],
        "values": [
            {"value": "John", "confidence": 0.95}
        ]
    }
}
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for full details.
