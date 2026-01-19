# LangState Core - Quick Reference

## Key Changes

### Two State Types

1. **Canonical State** - `{key: value}` - Business state for actions
2. **Interpretive State** - `{key: [{value, confidence}]}` - Tracks uncertainty

### Agent-Style Interface

LangState follows agent SDK conventions (similar to OpenAI Agents SDK):
- Main method is `invoke()` instead of `process_input()`
- Input is structured via `AgentInput` to support various interaction types
- Schema readers implement `BaseSchemaReader` interface

### New Flow

```
Schema → Canonical State → Interpretive State → [User Loop]
                                  ↓
                            Perceiver (updates interpretive)
                                  ↓
                            Canonicalizer (validates, triggers actions, updates canonical)
                                  ↓
                            Interpreter (generates UI)
```

### Component Updates

- **BaseSchemaReader**: Interface for schema loading (e.g., `OpenAPIYamlReader`)
- **schema_to_init_state()**: Creates canonical state (not interpretive)
- **canonical_to_interpretive_state()**: Converts canonical → interpretive (called once at init)
- **Perceiver**: Updates interpretive state with value-confidence pairs
- **Canonicalizer**: Receives interpretive state, validates, can trigger actions, returns canonical state
- **Interpreter**: Works with both states

### Usage Example

```python
from langstate import (
    LangState, LangStateConfig, AgentInput,
    BaseSchemaReader, OpenAPIYamlReader,
    BasePerceiver, BaseCanonicalizer, BaseInterpreter
)

# Create LangState with components
langstate = MyLangState(
    schema_reader=OpenAPIYamlReader(),
    perceiver=MyCustomPerceiver(),
    canonicalizer=MyLLMCanonicalizer(),
    interpreter=MyUIInterpreter()
)

# Or use setters
langstate = MyLangState()
langstate.set_schema_reader(OpenAPIYamlReader())
langstate.set_perceiver(MyCustomPerceiver())
langstate.set_canonicalizer(MyLLMCanonicalizer())
langstate.set_interpreter(MyUIInterpreter())

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

See [ARCHITECTURE.md](ARCHITECTURE.md) for full details.
