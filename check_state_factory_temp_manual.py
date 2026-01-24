#!/usr/bin/env python3
"""Quick verification script for StateFactory.

Creates a simple Schema, builds canonical and interpretive states
using `StateFactory`, and performs basic assertions.
"""
from packages.langstate.core.schema_reader.base.schema import Schema, SchemaField
from packages.langstate.core.state.factory.state_factory import StateFactory


def main() -> int:
    factory = StateFactory()

    # Define a simple schema with one defaulted and one empty field
    schema = Schema(
        {
            "name": SchemaField(
                field_id="name",
                field_type="string",
                label="Name",
                description="The person's name",
                required=True,
                validation_rules={},
                metadata={},
                default_value="Alice",
            ),
            "age": SchemaField(
                field_id="age",
                field_type="integer",
                label="Age",
                description="The person's age",
                required=False,
                validation_rules={},
                metadata={},
                default_value=None,
            ),
        }
    )

    # Create canonical state and verify default values are set
    canonical = factory.create_canonical_state(schema)
    canonical_dict = canonical.to_dict()
    assert canonical_dict.get("name") == "Alice", "Canonical name default missing"
    assert "age" in canonical_dict, "Canonical should contain 'age' key"

    # Create interpretive state and verify values were added with confidence 1.0
    interpretive = factory.create_interpretive_state(canonical)
    interpretive_dict = interpretive.to_dict()
    assert interpretive_dict.get("name") == "Alice", "Interpretive name default missing"
    best_name = interpretive.get_best_value("name")
    assert best_name is not None and best_name.value == "Alice", "Interpretive best value mismatch"
    assert best_name.confidence == 1.0, "Interpretive confidence should be 1.0 for canonical-sourced values"

    print("StateFactory check passed: canonical and interpretive states look correct.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
