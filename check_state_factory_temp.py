#!/usr/bin/env python3
"""Quick verification script for StateFactory.

Creates a simple Schema, builds canonical and interpretive states
using `StateFactory`, and performs basic assertions.
"""
from pathlib import Path
from packages.langstate.core.schema_reader.openapi.reader import OpenAPIReader
from packages.langstate.core.state.factory.state_factory import StateFactory


def main() -> int:
    factory = StateFactory()

    # Load schema from OpenAPI file using OpenAPIReader
    schema_path = Path(__file__).parent / "packages" / "langstate" / "tests" / "data" / "schemas" / "registeration.yaml"
    reader = OpenAPIReader("Registration")
    schema = reader.read(str(schema_path))

    # Create canonical state and verify default values are set
    canonical = factory.create_canonical_state(schema)
    canonical_dict = canonical.to_dict()
    assert canonical_dict.get("id") is None, "Canonical should contain 'id' key"

    # Create interpretive state and verify values were added with confidence 1.0
    interpretive = factory.create_interpretive_state(canonical)
    interpretive_dict = interpretive.to_dict()
    assert interpretive_dict.get("id") is None, "Interpretive should contain 'id' key"
    best_name = interpretive.get_best_value("name")
    assert best_name is not None and best_name.value == "Alice", "Interpretive best value mismatch"
    assert best_name.confidence == 1.0, "Interpretive confidence should be 1.0 for canonical-sourced values"

    print("StateFactory check passed: canonical and interpretive states look correct.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
