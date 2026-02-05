# LangState

LangState is a Python library for managing state in language-driven applications.
It models state as a schema-backed graph and keeps two synchronized views:
interpretive state (inferences + confidence) and canonical state (resolved values).
The core `LangState` orchestrator wires together spec extractors, mutators,
projectors, and actions to move from user input to validated state and UI output.

For architecture details, see `docs/ARCHITECTURE.md`.

## Local Development

Requirements: Python 3.10+ and Poetry.

```bash
cd packages/langstate
poetry install --with dev
```

Optional: open a Poetry shell so `python` and `pytest` use the project venv.

```bash
poetry shell
```

## Local Debugging

Run a focused test with stdout and breakpoints enabled:

```bash
poetry run pytest tests/unit/state/test_base_state.py -k snapshot -s
```

Debugging tips:
- Use `breakpoint()` in code; `pytest -s` will drop into `pdb`.
- To save integration test artifacts, set `TEST_OUTPUT=true`. Outputs land in `tests/integration/core/test_outputs`.

```bash
TEST_OUTPUT=true poetry run pytest tests/integration/core/test_state_from_openapi.py -s
```

## Running Tests

Run the full suite:

```bash
poetry run pytest
```

Run subsets:

```bash
poetry run pytest tests/unit
poetry run pytest tests/integration
```

Run a single test:

```bash
poetry run pytest tests/integration/core/test_state_from_openapi.py::TestSchemaParsing::test_schema_loads_successfully
```
