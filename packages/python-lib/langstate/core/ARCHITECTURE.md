# LangState Core Architecture

## Overview

LangState uses a dual-state architecture to separate interpretive data (with confidence) from canonical business state.

## State Types

### Canonical State

- **Format**: `{key: value}`
- **Purpose**: Business state for actions
- **Source**: Created from schema by `schema_to_init_state()`
- **Updated by**: Canonicalizer
- **Usage**: Final resolved values used for executing actions

### Interpretive State

- **Format**: `{key: [{value, confidence}]}`
- **Purpose**: Track multiple value possibilities with confidence scores
- **Source**: Created from canonical state by `canonical_to_interpretive_state()`
- **Updated by**: Perceiver
- **Usage**: Accumulates user inputs and evolves through conversation

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
┌──────────────────────┐
│ Interpretive State   │ {key: [{value, confidence}]}
│    (Initial)         │
└──────────────────────┘
     │
     │ User Input
     ▼
┌──────────────┐
│  Perceiver   │ Updates interpretive state
└──────┬───────┘ Adds value-confidence pairs
       │
       ▼
┌──────────────────────┐
│ Interpretive State   │ {key: [{value, confidence}]}
│    (Updated)         │
└──────┬───────────────┘
       │
       ▼
┌──────────────┐
│Canonicalizer │ Receives interpretive state
└──────┬───────┘ Validates, can trigger actions
       │         Updates canonical state
       ▼
┌──────────────────┐
│ Canonical State  │ {key: value}
│   (Updated)      │
└──────┬───────────┘
       │
       ▼
┌──────────────┐
│ Interpreter  │ Generates UI/prompts
└──────────────┘
```

## Component Responsibilities

### SchemaReaders

- Read schema definitions (YAML, JSON, OpenAPI)
- Convert to internal Schema DAG

### schema_to_init_state()

- Converts Schema → Canonical State
- Creates {key: value} structure
- Applies default values from schema

### canonical_to_interpretive_state()

- Converts Canonical State → Interpretive State
- Creates {key: [{value, confidence}]} structure
- Wraps default values with confidence 0.0
- **Called only once** at initialization

### Perceiver

- Receives user input (prompts, actions)
- Extracts field values from input
- **Updates interpretive state** by adding value-confidence pairs
- Returns updated interpretive state

### Canonicalizer

- **Receives interpretive state** as input
- Validates field values against constraints
- Resolves value-confidence pairs to single values
- **Checks if action can be triggered**
- **Can call action** when validation passes
- **Updates and returns canonical state**

### Interpreter

- Generates UI components
- Creates natural language prompts
- Determines next fields to focus on
- Works with both states for context

## Key Principles

1. **Separation of Concerns**
   - Interpretive state: Tracks uncertainty and evolution
   - Canonical state: Represents business logic and actions

2. **Single Responsibility**
   - Perceiver: Only updates interpretive state
   - Canonicalizer: Validates and updates canonical state, triggers actions

3. **One-Way Flow**
   - User Input → Perceiver → Interpretive State → Canonicalizer → Canonical State → Interpreter
   - Canonicalizer receives interpretive state, not perceiver output

4. **Action Triggering**
   - Actions are triggered by Canonicalizer
   - Only when validation passes
   - Based on canonical state completeness

## Example Implementation

```python
class MyLangState(LangState):
    async def initialize(self, config: LangStateConfig) -> InteractionRequest:
        # 1. Load schema
        schema = load_schema_from_openapi_yaml(config.schema_source)
        
        # 2. Create canonical state (key: value)
        self._canonical_state = schema_to_init_state(schema)
        
        # 3. Create interpretive state (key: [{value, confidence}])
        self._state = canonical_to_interpretive_state(self._canonical_state)

    async def process_input(self, user_input: str) -> Union[InteractionRequest, ActionResult]:
        # 1. Perceiver updates interpretive state
        perception = await self.perceiver.perceive(
            PerceptionContext(
                user_input=user_input,
                current_state=self._state,  # Interpretive state
                schema=self._schema
            )
        )
        self._state = perception.updated_state  # Updated interpretive state

        # 2. Canonicalizer validates and updates canonical state
        canonicalization = await self.canonicalizer.canonicalize(
            CanonicalizationContext(
                interpretive_state=self._state,  # Pass interpretive state
                canonical_state=self._canonical_state,
                schema=self._schema
            )
        )
        self._canonical_state = canonicalization.updated_state  # Updated canonical state
        
        # 3. Check if actions were triggered
        if canonicalization.actions_triggered:
            # Execute actions...
            pass

        # 4. Interpreter generates UI
        interpretation = await self.interpreter.interpret(
            InterpretationContext(
                current_state=self._state,  # Interpretive state
                canonical_state=self._canonical_state,  # Canonical state
                schema=self._schema
            )
        )

        # 5. Check if complete
        if self._is_state_complete(self._canonical_state):
            return ActionResult(
                state=self._state,
                canonical_state=self._canonical_state
            )

        return await self._create_interaction_request()
```

## Migration Notes

### Key Changes from Previous Architecture

1. **State Initialization**
   - Before: `schema_to_init_state()` created interpretive state
   - After: `schema_to_init_state()` creates canonical state, then `canonical_to_interpretive_state()` creates interpretive state

2. **Perceiver Output**
   - Before: Updated generic "state"
   - After: Explicitly updates interpretive state with value-confidence pairs

3. **Canonicalizer Input/Output**
   - Before: Received and returned generic "state"
   - After: Receives interpretive state, returns canonical state, can trigger actions

4. **Action Triggering**
   - Before: Separate mechanism
   - After: Canonicalizer checks validation and can trigger actions
