# LangState Core Architecture

## Overview

LangState is a single-state orchestrator:

- `LangState` persists one current state object in a repository.
- `Mutator` updates that state from user input.
- `Projectors` observe state changes and generate projections.
- `Action` contracts are kept in `core/action`, but are decoupled from
  `LangState`, `Mutator`, and `Projector` contracts.

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
│   │       ├── base.py         # BaseMutator abstract class
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
│   │   ├── base.py             # BaseState abstract class
│   │   ├── state.py            # State implementation
│   │   ├── schema.py           # StateSchema, StateField
│   │   ├── canonical/          # Canonical projection/state helpers
│   │   └── repository/
│   │       ├── base.py         # BaseStateRepository
│   │       └── memory.py       # InMemoryStateRepository
│   └── langstate/
│       └── base/
│           ├── langstate.py    # LangState orchestrator abstract class
│           └── schema.py       # AgentInput, InteractionRequest, StateResultData, LangStateConfig
└── docs/
    └── ARCHITECTURE.md
```

## LangState Orchestrator

### Key Responsibilities

- Initialize schema and components.
- Persist one current state in the configured repository.
- Notify projector observers when state is updated.
- Coordinate invocation flow.

### Main Methods

- `initialize(config)`: setup schema and components.
- `invoke(agent_input, metadata)`: process input and return next interaction or final state result.
- `get_state()`: access current state.
- `reset()`: reset state and restart flow.

### Component Management

- `set_spec_extractor()`, `remove_spec_extractor()`
- `set_mutator()`, `remove_mutator()`
- `set_projectors()`, `add_projector()`, `remove_projector()`, `clear_projectors()`
- `set_state_repository()`

## State Model

At the orchestrator level, LangState tracks one state ID (`state`) and one state object.

The default schema payload shape is:

```python
{
    "field_key": {
        "inference": [{"content": "...", "mutator_id": "..."}],
        "values": [{"value": "...", "confidence": 0.95}]
    }
}
```

This shape is represented by `StateSchema`.

## Data Flow

```text
┌──────────┐
│  Schema  │
└────┬─────┘
     │ initialize
     ▼
┌──────────────────────┐
│ Current State (repo) │
└────┬─────────────────┘
     │ user input
     ▼
┌──────────────┐
│   Mutator    │
└──────┬───────┘
       │ mutate(state)
       ▼
┌──────────────────────┐
│ Current State (save) │
└──────┬───────────────┘
       │ notify(context)
       ▼
┌──────────────────────────────────────────────┐
│ Projector observers (UI, canonical, custom)  │
└──────────────────────────────────────────────┘
```

## Observer Pattern

LangState uses the generic observer protocol in `core/data_structure/observer`:

- `LangState` is a `Subject`.
- Each projector is an `Observer`.
- `LangState` calls `await notify(context)` after `_set_state(...)`.
- Projectors run through `notified(...)`, which delegates to `project(...)`.

## Projector Contracts

- `ProjectionContext` carries shared fields: `state`, `conversation_history`,
  `user_preferences`, `strategy`, `confidence_threshold`, `metadata`.
- Specialized projector modules (`ui`, `canonical`) keep their own result types
  and can extend behavior without LangState branching on projector type.

## Mutator Contract

- `MutationContext` contains `input`, `state`, and optional `metadata`.
- `MutationResult` returns updated `state`.

## Action Contract

`core/action` remains available for business execution contracts.
It is intentionally not wired into LangState core orchestration contracts.
