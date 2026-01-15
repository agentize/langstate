# LangState Core - Quick Reference

## Key Changes

### Two State Types

1. **Canonical State** - `{key: value}` - Business state for actions
2. **Interpretive State** - `{key: [{value, confidence}]}` - Tracks uncertainty

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

- **schema_to_init_state()**: Creates canonical state (not interpretive)
- **canonical_to_interpretive_state()**: New function, converts canonical → interpretive (called once at init)
- **Perceiver**: Updates interpretive state with value-confidence pairs
- **Canonicalizer**: Receives interpretive state, validates, can trigger actions, returns canonical state
- **Interpreter**: Works with both states

### Usage Example

```python
# Initialize
canonical_state = schema_to_init_state(schema)
interpretive_state = canonical_to_interpretive_state(canonical_state)

# Process input
perception = perceiver.perceive(interpretive_state)  # Updates interpretive
interpretive_state = perception.updated_state

canonicalization = canonicalizer.canonicalize(interpretive_state, canonical_state)
canonical_state = canonicalization.updated_state  # Updates canonical
if canonicalization.actions_triggered:
    # Execute actions
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for full details.
