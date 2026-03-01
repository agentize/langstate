# Evaluator

The **Evaluator** module is responsible for testing how well a `Mutator` transforms a given state. It runs the mutator against a pre-state and a structured input, captures the resulting post-state, and produces a detailed field-by-field comparison against an expected post-state.

---

## Architecture overview

```python
EvaluationContext
  ├── mutator          BaseMutator[MutationContext]
  ├── pre_state        BaseState
  ├── expected_post_state  BaseState
  ├── mutation_input   StructuredInput
  └── metadata?        Dict[str, Any]

BaseEvaluator (ABC)
  └── Evaluator                ← shared _compare_states / _values_equal logic
        └── LLMEvaluator       ← concrete evaluate() implementation

EvaluationResult
  ├── comparison       StateComparison
  ├── actual_post_state  BaseState
  ├── accuracy_score   float  [0.0 – 1.0]
  ├── time_used        float  (seconds)
  └── metadata?        Dict[str, Any]
```

---

## Classes

### `BaseEvaluator` (`base.py`)

Abstract base class. All evaluator implementations must subclass this and provide:

| Method            | Signature                                                | Description                                  |
| ----------------- | -------------------------------------------------------- | -------------------------------------------- |
| `evaluate`        | `async (context: EvaluationContext) -> EvaluationResult` | Orchestrates mutation and comparison.        |
| `_compare_states` | `async (expected, actual: BaseState) -> StateComparison` | Produces a field-by-field comparison report. |

---

### `Evaluator` (`evaluator.py`)

Concrete base class that implements the shared comparison logic. Subclasses only need to implement `evaluate()`.

#### `_compare_states(expected, actual) -> StateComparison`

Iterates over the union of all field paths from `expected` and `actual`, retrieves the best `ValueConfidence` for each path, and classifies each field as:

| Classification | Condition                                                  |
| -------------- | ---------------------------------------------------------- |
| **matching**   | Field present in both; `value` and `confidence` are equal. |
| **mismatched** | Field present in both; values differ.                      |
| **missing**    | Field present only in `expected`.                          |
| **extra**      | Field present only in `actual`.                            |

`overall_match` on the resulting `StateComparison` is `True` only when there are zero mismatched, missing, and extra fields.

#### `_values_equal(a, b) -> bool`

Two `ValueConfidence` instances are considered equal when both `value` and `confidence` match. Two `None` values are also treated as equal.

---

### `LLMEvaluator` (`llm/evaluator.py`)

The production-ready implementation of `Evaluator`. Inherits `_compare_states` from `Evaluator` and provides `evaluate()`.

#### `evaluate(context: EvaluationContext) -> EvaluationResult`

Execution steps:

1. **Copy pre-state** — calls `context.pre_state.copy()` so the original is not modified. Raises `TypeError` if the copy is not a `State`.
2. **Build `MutationContext`** — wraps the state copy, input (`StructuredInput`), and optional metadata.
3. **Run mutator** — calls `context.mutator.mutate(mutation_context)` and measures wall-clock time with `time.monotonic`.
4. **Compare states** — delegates to `_compare_states(expected_post_state, actual_post_state)`.
5. **Compute accuracy score** — `matching_fields / (matching + mismatched + missing)`. Returns `0.0` if there are no expected fields.
6. **Return `EvaluationResult`**.

---

## Schemas (`schema.py`)

### `EvaluationContext`

| Field                 | Type                           | Description                                     |
| --------------------- | ------------------------------ | ----------------------------------------------- |
| `mutator`             | `BaseMutator[MutationContext]` | The mutator instance to evaluate.               |
| `pre_state`           | `BaseState`                    | The interpretive state before mutation.         |
| `expected_post_state` | `BaseState`                    | The expected interpretive state after mutation. |
| `mutation_input`      | `StructuredInput`              | The structured input fed to the mutator.        |
| `metadata`            | `Dict[str, Any] \| None`       | Optional additional metadata.                   |

---

### `FieldComparison`

Comparison result for a single field path.

| Field            | Type                      | Description                                                    |
| ---------------- | ------------------------- | -------------------------------------------------------------- |
| `field_path`     | `str`                     | Dot-separated path of the compared field.                      |
| `matches`        | `bool`                    | Whether expected and actual values are equal.                  |
| `expected_value` | `ValueConfidence \| None` | Best value from the expected state; `None` if field is absent. |
| `actual_value`   | `ValueConfidence \| None` | Best value from the actual state; `None` if field is absent.   |
| `difference`     | `str \| None`             | Human-readable mismatch description; `None` when matching.     |

---

### `StateComparison`

Aggregated result of comparing two interpretive states.

| Field               | Type                    | Description                                                   |
| ------------------- | ----------------------- | ------------------------------------------------------------- |
| `fields`            | `List[FieldComparison]` | Per-field comparison details, sorted by path.                 |
| `matching_fields`   | `int`                   | Count of fully matching fields.                               |
| `mismatched_fields` | `int`                   | Count of fields present in both states with differing values. |
| `missing_fields`    | `int`                   | Count of fields in expected state absent from actual.         |
| `extra_fields`      | `int`                   | Count of fields in actual state absent from expected.         |
| `overall_match`     | `bool`                  | `True` when `mismatched == missing == extra == 0`.            |

---

### `EvaluationResult`

| Field               | Type                     | Description                                                         |
| ------------------- | ------------------------ | ------------------------------------------------------------------- |
| `comparison`        | `StateComparison`        | Detailed field-by-field comparison report.                          |
| `actual_post_state` | `BaseState`              | The actual post-state produced by the mutator.                      |
| `accuracy_score`    | `float`                  | `matching / (matching + mismatched + missing)`, range `[0.0, 1.0]`. |
| `time_used`         | `float`                  | Wall-clock time of the `mutate()` call, in seconds.                 |
| `metadata`          | `Dict[str, Any] \| None` | Optional metadata echoed from the evaluation context.               |

---

## Public API (`__init__.py`)

```python
from langstate.core.evaluator import (
    BaseEvaluator,
    Evaluator,
    LLMEvaluator,
    EvaluationContext,
    EvaluationResult,
    FieldComparison,
    StateComparison,
)
```

---

## Usage example

```python
import asyncio
from langstate.core.evaluator import LLMEvaluator, EvaluationContext
from langstate.core.mutator.llm.schema import StructuredInput

evaluator = LLMEvaluator()

result = await evaluator.evaluate(
    EvaluationContext(
        mutator=my_mutator,
        pre_state=pre_state,
        expected_post_state=expected_state,
        mutation_input=StructuredInput(prompt="my name is John"),
    )
)

print(result.accuracy_score)           # e.g. 0.85
print(result.comparison.overall_match) # True / False
print(result.time_used)                # seconds elapsed

for field in result.comparison.fields:
    if not field.matches:
        print(f"{field.field_path}: {field.difference}")
```

---

## Accuracy score formula

$$
\text{accuracy\_score} = \frac{\text{matching\_fields}}{\text{matching\_fields} + \text{mismatched\_fields} + \text{missing\_fields}}
$$

Extra fields (present in the actual state but not expected) do **not** penalise the score. The score is `0.0` when there are no expected fields at all.
