"""Unit tests for StateFactory implementation.

Tests the StateFactory class that creates CanonicalState and InterpretiveState
instances from schemas.
"""

# pyright: reportPrivateUsage=false

from core.schema_reader.base.schema import Schema, SchemaField
from core.state.canonical.state import CanonicalState
from core.state.factory.state_factory import StateFactory
from core.state.interpretive.state import InterpretiveState


class TestStateFactoryCreateCanonicalState:
    """Tests for create_canonical_state operation."""

    def test_create_from_empty_schema(self) -> None:
        """Should create empty state from empty schema."""
        factory = StateFactory()
        schema = Schema.model_validate({})

        state = factory.create_canonical_state(schema)

        assert isinstance(state, CanonicalState)
        assert len(state.get_all_fields()) == 0

    def test_create_with_simple_fields(self) -> None:
        """Should create state with simple fields from schema."""
        factory = StateFactory()
        schema = Schema.model_validate(
            {
                "name": SchemaField(
                    field_id="name", field_type="string", default_value=None
                ),
                "email": SchemaField(
                    field_id="email", field_type="string", default_value=None
                ),
            }
        )

        state = factory.create_canonical_state(schema)

        assert state.get_field("name") is None
        assert state.get_field("email") is None

    def test_create_with_default_values(self) -> None:
        """Should initialize fields with default values from schema."""
        factory = StateFactory()
        schema = Schema.model_validate(
            {
                "name": SchemaField(
                    field_id="name", field_type="string", default_value="John Doe"
                ),
                "age": SchemaField(
                    field_id="age", field_type="integer", default_value=25
                ),
                "active": SchemaField(
                    field_id="active", field_type="boolean", default_value=True
                ),
            }
        )

        state = factory.create_canonical_state(schema)

        assert state.get_field("name") == "John Doe"
        assert state.get_field("age") == 25
        assert state.get_field("active") is True

    def test_create_with_nested_object(self) -> None:
        """Should create state with nested object fields."""
        factory = StateFactory()
        schema = Schema.model_validate(
            {
                "address": SchemaField(
                    field_id="address",
                    field_type="object",
                    default_value={
                        "city": SchemaField(
                            field_id="city",
                            field_type="string",
                            default_value="New York",
                        ),
                        "country": SchemaField(
                            field_id="country", field_type="string", default_value="USA"
                        ),
                    },
                ),
            }
        )

        state = factory.create_canonical_state(schema)

        assert state.get_field("address.city") == "New York"
        assert state.get_field("address.country") == "USA"
        # Parent node should not be created as a leaf
        assert state.get_field("address") is None

    def test_create_with_deeply_nested_object(self) -> None:
        """Should handle deeply nested object structures."""
        factory = StateFactory()
        schema = Schema.model_validate(
            {
                "user": SchemaField(
                    field_id="user",
                    field_type="object",
                    default_value={
                        "profile": SchemaField(
                            field_id="profile",
                            field_type="object",
                            default_value={
                                "name": SchemaField(
                                    field_id="name",
                                    field_type="string",
                                    default_value="John",
                                ),
                            },
                        ),
                    },
                ),
            }
        )

        state = factory.create_canonical_state(schema)

        assert state.get_field("user.profile.name") == "John"

    def test_create_with_mixed_fields(self) -> None:
        """Should handle mix of simple and nested fields."""
        factory = StateFactory()
        schema = Schema.model_validate(
            {
                "id": SchemaField(
                    field_id="id", field_type="string", default_value="123"
                ),
                "address": SchemaField(
                    field_id="address",
                    field_type="object",
                    default_value={
                        "city": SchemaField(
                            field_id="city", field_type="string", default_value="NYC"
                        ),
                    },
                ),
            }
        )

        state = factory.create_canonical_state(schema)

        assert state.get_field("id") == "123"
        assert state.get_field("address.city") == "NYC"

    def test_create_with_list_default_value(self) -> None:
        """Should handle list default values."""
        factory = StateFactory()
        tags_list = ["tag1", "tag2"]
        schema = Schema.model_validate(
            {
                "tags": SchemaField(
                    field_id="tags", field_type="array", default_value=tags_list
                ),
            }
        )

        state = factory.create_canonical_state(schema)

        assert state.get_field("tags") == tags_list

    def test_create_with_empty_dict_default_value(self) -> None:
        """Should handle empty dict default value (not nested schema)."""
        factory = StateFactory()
        schema = Schema.model_validate(
            {
                "metadata": SchemaField(
                    field_id="metadata", field_type="object", default_value={}
                ),
            }
        )

        state = factory.create_canonical_state(schema)

        # Empty dict is treated as a leaf value (not nested schema)
        assert state.get_field("metadata") == {}


class TestStateFactoryCreateInterpretiveState:
    """Tests for create_interpretive_state operation."""

    def test_create_from_empty_canonical(self) -> None:
        """Should create empty interpretive state from empty canonical."""
        factory = StateFactory()
        canonical = CanonicalState()

        interpretive = factory.create_interpretive_state(canonical)

        assert isinstance(interpretive, InterpretiveState)
        assert len(interpretive.get_all_fields()) == 0

    def test_create_with_simple_values(self) -> None:
        """Should create interpretive state with values from canonical."""
        factory = StateFactory()
        canonical = CanonicalState()
        canonical.set_field("name", "John")
        canonical.set_field("email", "john@test.com")

        interpretive = factory.create_interpretive_state(canonical)

        name_best = interpretive.get_best_value("name")
        email_best = interpretive.get_best_value("email")

        assert name_best is not None
        assert name_best.value == "John"
        assert name_best.confidence == 1.0

        assert email_best is not None
        assert email_best.value == "john@test.com"
        assert email_best.confidence == 1.0

    def test_create_with_none_values(self) -> None:
        """Should handle None values from canonical state."""
        factory = StateFactory()
        canonical = CanonicalState()
        canonical.set_field("name", None)

        interpretive = factory.create_interpretive_state(canonical)

        best = interpretive.get_best_value("name")
        assert best is not None
        assert best.value is None
        assert best.confidence == 1.0

    def test_create_with_nested_paths(self) -> None:
        """Should preserve nested paths from canonical state."""
        factory = StateFactory()
        canonical = CanonicalState()
        canonical.set_field("address.city", "NYC")
        canonical.set_field("address.country", "USA")

        interpretive = factory.create_interpretive_state(canonical)

        city_best = interpretive.get_best_value("address.city")
        country_best = interpretive.get_best_value("address.country")

        assert city_best is not None
        assert city_best.value == "NYC"

        assert country_best is not None
        assert country_best.value == "USA"

    def test_create_with_various_types(self) -> None:
        """Should handle various value types from canonical."""
        factory = StateFactory()
        canonical = CanonicalState()
        canonical.set_field("string", "text")
        canonical.set_field("number", 42)
        canonical.set_field("float", 3.14)
        canonical.set_field("bool", True)

        interpretive = factory.create_interpretive_state(canonical)

        assert interpretive.get_best_value("string") is not None
        assert interpretive.get_best_value("string").value == "text"  # type: ignore[union-attr]

        assert interpretive.get_best_value("number") is not None
        assert interpretive.get_best_value("number").value == 42  # type: ignore[union-attr]

        assert interpretive.get_best_value("float") is not None
        assert interpretive.get_best_value("float").value == 3.14  # type: ignore[union-attr]

        assert interpretive.get_best_value("bool") is not None
        assert interpretive.get_best_value("bool").value is True  # type: ignore[union-attr]


class TestStateFactoryInitializeLeafFields:
    """Tests for _initialize_leaf_fields private method."""

    def test_initialize_with_empty_fields(self) -> None:
        """Should handle empty fields dict."""
        factory = StateFactory()
        state = CanonicalState()

        factory._initialize_leaf_fields(state, {}, prefix="")

        assert len(state.get_all_fields()) == 0

    def test_initialize_with_prefix(self) -> None:
        """Should use prefix for field paths."""
        factory = StateFactory()
        state = CanonicalState()
        fields = {
            "city": SchemaField(
                field_id="city", field_type="string", default_value="NYC"
            ),
        }

        factory._initialize_leaf_fields(state, fields, prefix="address.")

        assert state.get_field("address.city") == "NYC"

    def test_initialize_skips_nested_schema_fields(self) -> None:
        """Should recursively initialize nested schema fields."""
        factory = StateFactory()
        state = CanonicalState()
        fields = {
            "address": SchemaField(
                field_id="address",
                field_type="object",
                default_value={
                    "city": SchemaField(
                        field_id="city", field_type="string", default_value="NYC"
                    ),
                },
            ),
        }

        factory._initialize_leaf_fields(state, fields, prefix="")

        # Nested leaf should be created
        assert state.get_field("address.city") == "NYC"
        # Parent should not be created as leaf
        assert state.get_field("address") is None


class TestStateFactoryIntegration:
    """Integration tests for StateFactory workflow."""

    def test_full_workflow(self) -> None:
        """Test complete workflow from schema to interpretive state."""
        factory = StateFactory()

        # Create schema
        schema = Schema.model_validate(
            {
                "name": SchemaField(
                    field_id="name", field_type="string", default_value="Default Name"
                ),
                "email": SchemaField(
                    field_id="email", field_type="string", default_value=None
                ),
            }
        )

        # Create canonical state from schema
        canonical = factory.create_canonical_state(schema)

        assert canonical.get_field("name") == "Default Name"
        assert canonical.get_field("email") is None

        # Update canonical state
        canonical.set_field("email", "user@test.com")

        # Create interpretive state from canonical
        interpretive = factory.create_interpretive_state(canonical)

        name_best = interpretive.get_best_value("name")
        email_best = interpretive.get_best_value("email")

        assert name_best is not None
        assert name_best.value == "Default Name"

        assert email_best is not None
        assert email_best.value == "user@test.com"

    def test_nested_workflow(self) -> None:
        """Test workflow with nested schema."""
        factory = StateFactory()

        schema = Schema.model_validate(
            {
                "user": SchemaField(
                    field_id="user",
                    field_type="object",
                    default_value={
                        "name": SchemaField(
                            field_id="name", field_type="string", default_value="John"
                        ),
                        "contact": SchemaField(
                            field_id="contact",
                            field_type="object",
                            default_value={
                                "email": SchemaField(
                                    field_id="email",
                                    field_type="string",
                                    default_value=None,
                                ),
                            },
                        ),
                    },
                ),
            }
        )

        canonical = factory.create_canonical_state(schema)

        assert canonical.get_field("user.name") == "John"
        assert canonical.get_field("user.contact.email") is None

        interpretive = factory.create_interpretive_state(canonical)

        name_best = interpretive.get_best_value("user.name")
        assert name_best is not None
        assert name_best.value == "John"


class TestStateFactoryEdgeCases:
    """Tests for edge cases in StateFactory."""

    def test_schema_field_with_non_schemafield_dict_value(self) -> None:
        """Should treat non-SchemaField dict as leaf value."""
        factory = StateFactory()
        metadata_dict: dict[str, object] = {"key": "value", "count": 5}
        schema = Schema.model_validate(
            {
                "metadata": SchemaField(
                    field_id="metadata",
                    field_type="object",
                    default_value=metadata_dict,
                ),
            }
        )

        state = factory.create_canonical_state(schema)

        # Should be stored as leaf value
        assert state.get_field("metadata") == metadata_dict

    def test_instance_independence(self) -> None:
        """Created states should be independent instances."""
        factory = StateFactory()
        schema = Schema.model_validate(
            {
                "name": SchemaField(
                    field_id="name", field_type="string", default_value="Default"
                ),
            }
        )

        state1 = factory.create_canonical_state(schema)
        state2 = factory.create_canonical_state(schema)

        state1.set_field("name", "Changed")

        assert state1.get_field("name") == "Changed"
        assert state2.get_field("name") == "Default"
