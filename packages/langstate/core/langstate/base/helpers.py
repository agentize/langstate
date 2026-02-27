"""Helpers for the LangState orchestrator.

Provides utilities for converting between schema definitions and state objects.
"""

from typing import List, cast

from ...spec_extractor.base.schema import Schema
from ...state.state.schema import InterpretiveField
from ...state.state.state import State


def schema_to_state(schema: Schema) -> State:
    """Convert a :class:`Schema` into an empty :class:`State`.

    Each field defined in the schema is registered in the State's DAH
    as an empty :class:`InterpretiveField` (no values, no inference).
    Dependencies declared via ``validation_rules["depends_on"]`` are
    added as hyperedges.

    Args:
        schema: The parsed schema definition.

    Returns:
        A new ``State`` with one node per schema field, ready for mutation.
    """
    state = State()

    for field_id, field_def in schema.root.items():
        state.set_field(field_id, InterpretiveField())

        # Propagate schema-level dependency information.
        depends_on = field_def.validation_rules.get("depends_on")
        if isinstance(depends_on, list):
            for dep in cast(List[object], depends_on):
                if isinstance(dep, str):
                    # Ensure the dependency node exists.
                    if state.get_field(dep) is None:
                        state.set_field(dep, InterpretiveField())
                    state.add_field_dependency(parent_path=dep, child_path=field_id)

    return state
