"""Unit tests for schema_to_state helper.

Covers all branches in the conversion of a Schema into a State,
including dependency propagation and edge cases.
"""

from core.langstate.base.helpers import schema_to_state
from core.spec_extractor.base.schema import Schema, SchemaField
from core.state.state.schema import InterpretiveField


class TestSchemaToStateBasic:
    """Basic conversion tests."""

    def test_empty_schema_returns_empty_state(self) -> None:
        schema = Schema.model_validate({})
        state = schema_to_state(schema)
        assert state.get_all_fields() == {}

    def test_single_field(self) -> None:
        schema = Schema.model_validate(
            {
                "name": SchemaField(
                    field_id="name",
                    field_type="string",
                    label="Name",
                ),
            }
        )
        state = schema_to_state(schema)
        field = state.get_field("name")
        assert field is not None
        assert isinstance(field, InterpretiveField)
        assert len(field.values) == 0
        assert field.inference is None

    def test_multiple_fields(self) -> None:
        schema = Schema.model_validate(
            {
                "name": SchemaField(field_id="name", field_type="string", label="Name"),
                "email": SchemaField(
                    field_id="email", field_type="string", label="Email"
                ),
                "age": SchemaField(field_id="age", field_type="integer", label="Age"),
            }
        )
        state = schema_to_state(schema)
        assert state.get_field("name") is not None
        assert state.get_field("email") is not None
        assert state.get_field("age") is not None


class TestSchemaToStateDependencies:
    """Dependency propagation tests."""

    def test_depends_on_list_creates_hyperedge(self) -> None:
        schema = Schema.model_validate(
            {
                "country": SchemaField(
                    field_id="country",
                    field_type="string",
                    label="Country",
                ),
                "city": SchemaField(
                    field_id="city",
                    field_type="string",
                    label="City",
                    validation_rules={"depends_on": ["country"]},
                ),
            }
        )
        state = schema_to_state(schema)
        children = list(state.get_children("country"))
        assert "city" in children

    def test_depends_on_nonexistent_field_creates_it(self) -> None:
        """If dependency target doesn't exist in the schema, it's auto-created."""
        schema = Schema.model_validate(
            {
                "city": SchemaField(
                    field_id="city",
                    field_type="string",
                    label="City",
                    validation_rules={"depends_on": ["region"]},
                ),
            }
        )
        state = schema_to_state(schema)
        # "region" wasn't in the schema but should have been auto-created
        assert state.get_field("region") is not None
        children = list(state.get_children("region"))
        assert "city" in children

    def test_depends_on_non_string_entries_skipped(self) -> None:
        """Non-string entries in depends_on list should be skipped."""
        schema = Schema.model_validate(
            {
                "city": SchemaField(
                    field_id="city",
                    field_type="string",
                    label="City",
                    validation_rules={"depends_on": [42, None, "country"]},
                ),
                "country": SchemaField(
                    field_id="country",
                    field_type="string",
                    label="Country",
                ),
            }
        )
        state = schema_to_state(schema)
        # Only "country" (the string) should create an edge
        children = list(state.get_children("country"))
        assert "city" in children

    def test_depends_on_not_a_list_is_ignored(self) -> None:
        """If depends_on is not a list, it should be ignored."""
        schema = Schema.model_validate(
            {
                "city": SchemaField(
                    field_id="city",
                    field_type="string",
                    label="City",
                    validation_rules={"depends_on": "country"},
                ),
            }
        )
        state = schema_to_state(schema)
        assert state.get_field("city") is not None
        # No errors, just no dependency edges

    def test_multiple_dependencies(self) -> None:
        schema = Schema.model_validate(
            {
                "a": SchemaField(field_id="a", field_type="string", label="A"),
                "b": SchemaField(field_id="b", field_type="string", label="B"),
                "c": SchemaField(
                    field_id="c",
                    field_type="string",
                    label="C",
                    validation_rules={"depends_on": ["a", "b"]},
                ),
            }
        )
        state = schema_to_state(schema)
        children_a = list(state.get_children("a"))
        children_b = list(state.get_children("b"))
        assert "c" in children_a
        assert "c" in children_b

    def test_no_validation_rules_key(self) -> None:
        """Fields without depends_on in validation_rules should work fine."""
        schema = Schema.model_validate(
            {
                "name": SchemaField(
                    field_id="name",
                    field_type="string",
                    label="Name",
                    validation_rules={"min_length": 1},
                ),
            }
        )
        state = schema_to_state(schema)
        assert state.get_field("name") is not None
