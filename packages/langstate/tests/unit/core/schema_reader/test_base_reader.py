"""
Comprehensive unit tests for Schema Reader base module.

Tests cover:
- SchemaField dataclass with all fields
- Schema (RootModel) functionality
- SourceType enum
- BaseSchemaReader abstract interface

Target: 100% code coverage for schema_reader/base/schema.py and reader.py
"""

from __future__ import annotations

import pytest
from typing import Any, Dict

from core.schema_reader.base.schema import (
    Schema,
    SchemaField,
    SourceType,
)
from core.schema_reader.base.reader import BaseSchemaReader


# ============================================================================
# Test SchemaField
# ============================================================================


class TestSchemaField:
    """Tests for SchemaField dataclass."""

    def test_schema_field_minimal(self) -> None:
        """SchemaField with only required fields."""
        field = SchemaField(field_id="test_field")

        assert field.field_id == "test_field"
        assert field.field_type == "string"  # default
        assert field.label == ""  # default
        assert field.description == ""  # default
        assert field.required is False  # default
        assert field.default_value is None  # default
        assert field.validation_rules == {}  # default
        assert field.metadata == {}  # default

    def test_schema_field_all_fields(self) -> None:
        """SchemaField with all fields populated."""
        field = SchemaField(
            field_id="user_email",
            field_type="string:email",
            label="Email Address",
            description="User's primary email address",
            required=True,
            default_value="user@example.com",
            validation_rules={"pattern": r"^[\w\.-]+@[\w\.-]+\.\w+$"},
            metadata={"x-sup": {"constraints": ["user_id"]}},
        )

        assert field.field_id == "user_email"
        assert field.field_type == "string:email"
        assert field.label == "Email Address"
        assert field.description == "User's primary email address"
        assert field.required is True
        assert field.default_value == "user@example.com"
        assert field.validation_rules == {"pattern": r"^[\w\.-]+@[\w\.-]+\.\w+$"}
        assert field.metadata == {"x-sup": {"constraints": ["user_id"]}}

    def test_schema_field_model_dump(self) -> None:
        """SchemaField should support model_dump for serialization."""
        field = SchemaField(
            field_id="name", field_type="string", label="Name", required=True
        )

        data = field.model_dump()

        assert data["field_id"] == "name"
        assert data["field_type"] == "string"
        assert data["label"] == "Name"
        assert data["required"] is True

    def test_schema_field_different_types(self) -> None:
        """SchemaField should support various field types."""
        # Integer field
        int_field = SchemaField(
            field_id="age",
            field_type="integer",
            validation_rules={"minimum": 0, "maximum": 150},
        )
        assert int_field.field_type == "integer"

        # Boolean field
        bool_field = SchemaField(
            field_id="active", field_type="boolean", default_value=True
        )
        assert bool_field.field_type == "boolean"
        assert bool_field.default_value is True

        # Array field
        array_field = SchemaField(
            field_id="tags",
            field_type="array<string>",
            validation_rules={"minItems": 1, "maxItems": 10},
        )
        assert array_field.field_type == "array<string>"

    def test_schema_field_nested_default_value(self) -> None:
        """SchemaField with nested object as default_value."""
        nested_fields = {
            "street": SchemaField(field_id="street", field_type="string"),
            "city": SchemaField(field_id="city", field_type="string"),
        }

        field = SchemaField(
            field_id="address", field_type="object", default_value=nested_fields
        )

        assert field.field_id == "address"
        assert field.field_type == "object"
        assert isinstance(field.default_value, dict)
        assert "street" in field.default_value  # type: ignore
        assert "city" in field.default_value  # type: ignore


# ============================================================================
# Test SourceType Enum
# ============================================================================


class TestSourceType:
    """Tests for SourceType enum."""

    def test_source_type_values(self) -> None:
        """SourceType should have expected values."""
        assert SourceType.YAML.value == "yaml"
        assert SourceType.JSON.value == "json"
        assert SourceType.OPENAPI.value == "openapi"
        assert SourceType.CUSTOM.value == "custom"
        assert SourceType.UNKNOWN.value == "unknown"

    def test_source_type_is_string_enum(self) -> None:
        """SourceType should be a string enum."""
        assert isinstance(SourceType.YAML, str)
        assert SourceType.YAML == "yaml"

    def test_source_type_all_members(self) -> None:
        """SourceType should have all expected members."""
        members = list(SourceType)
        assert len(members) == 5
        assert SourceType.YAML in members
        assert SourceType.JSON in members
        assert SourceType.OPENAPI in members
        assert SourceType.CUSTOM in members
        assert SourceType.UNKNOWN in members


# ============================================================================
# Test Schema (RootModel)
# ============================================================================


class TestSchema:
    """Tests for Schema RootModel."""

    def test_schema_creation_empty(self) -> None:
        """Schema can be created with empty dict."""
        schema = Schema(root={})

        assert schema.root == {}

    def test_schema_creation_with_fields(self) -> None:
        """Schema can be created with field definitions."""
        fields = {
            "name": SchemaField(
                field_id="name", field_type="string", label="Full Name", required=True
            ),
            "email": SchemaField(
                field_id="email",
                field_type="string:email",
                label="Email Address",
                required=True,
            ),
        }

        schema = Schema(root=fields)

        assert len(schema.root) == 2
        assert "name" in schema.root
        assert "email" in schema.root
        assert schema.root["name"].field_id == "name"
        assert schema.root["email"].field_type == "string:email"

    def test_schema_model_dump(self) -> None:
        """Schema should support model_dump for serialization."""
        fields = {
            "id": SchemaField(field_id="id", field_type="string"),
        }

        schema = Schema(root=fields)
        data = schema.model_dump()

        assert "id" in data
        assert data["id"]["field_id"] == "id"

    def test_schema_iteration(self) -> None:
        """Schema root can be iterated."""
        fields = {
            "field1": SchemaField(field_id="field1"),
            "field2": SchemaField(field_id="field2"),
        }

        schema = Schema(root=fields)

        keys = list(schema.root.keys())
        assert "field1" in keys
        assert "field2" in keys

    def test_schema_complex_structure(self) -> None:
        """Schema with complex nested structure."""
        # Nested object fields
        person_fields = {
            "name": SchemaField(field_id="name", field_type="string"),
            "email": SchemaField(field_id="email", field_type="string:email"),
        }

        fields = {
            "registrant": SchemaField(
                field_id="registrant",
                field_type="object<Person>",
                default_value=person_fields,
            ),
            "event_id": SchemaField(
                field_id="event_id", field_type="string", required=True
            ),
            "guests": SchemaField(
                field_id="guests",
                field_type="array<object<Guest>>",
                validation_rules={"minItems": 0, "maxItems": 49},
            ),
        }

        schema = Schema(root=fields)

        assert len(schema.root) == 3
        assert schema.root["registrant"].field_type == "object<Person>"
        assert schema.root["guests"].validation_rules["maxItems"] == 49


# ============================================================================
# Test BaseSchemaReader Abstract Interface
# ============================================================================


class TestBaseSchemaReaderInterface:
    """Tests for BaseSchemaReader abstract interface."""

    def test_base_schema_reader_cannot_be_instantiated(self) -> None:
        """BaseSchemaReader should not be directly instantiable."""
        with pytest.raises(TypeError):
            BaseSchemaReader()  # type: ignore

    def test_concrete_implementation_works(self) -> None:
        """Concrete implementation of BaseSchemaReader should work."""

        class MockSchemaReader(BaseSchemaReader):
            """Mock implementation for testing."""

            def read(self, source: Any) -> Schema:
                return Schema(root={"test": SchemaField(field_id="test")})

        reader = MockSchemaReader()
        result = reader.read("mock_source")

        assert isinstance(result, Schema)
        assert "test" in result.root

    def test_concrete_implementation_with_file_path(self) -> None:
        """Concrete implementation should accept file path."""
        from pathlib import Path

        class FileSchemaReader(BaseSchemaReader):
            """File-based schema reader for testing."""

            def read(self, source: Any) -> Schema:
                # Simulate reading from file path
                if isinstance(source, (str, Path)):
                    return Schema(root={"from_file": SchemaField(field_id="from_file")})
                raise ValueError("Invalid source")

        reader = FileSchemaReader()

        # Test with string path
        result_str = reader.read("/path/to/schema.yaml")
        assert "from_file" in result_str.root

        # Test with Path object
        result_path = reader.read(Path("/path/to/schema.yaml"))
        assert "from_file" in result_path.root


# ============================================================================
# Test SchemaField Edge Cases
# ============================================================================


class TestSchemaFieldEdgeCases:
    """Edge case tests for SchemaField."""

    def test_schema_field_empty_validation_rules(self) -> None:
        """SchemaField with explicitly empty validation rules."""
        field = SchemaField(field_id="test", validation_rules={})

        assert field.validation_rules == {}

    def test_schema_field_empty_metadata(self) -> None:
        """SchemaField with explicitly empty metadata."""
        field = SchemaField(field_id="test", metadata={})

        assert field.metadata == {}

    def test_schema_field_complex_validation_rules(self) -> None:
        """SchemaField with complex validation rules."""
        field = SchemaField(
            field_id="password",
            field_type="string",
            validation_rules={
                "minLength": 8,
                "maxLength": 128,
                "pattern": r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)",
            },
        )

        assert field.validation_rules["minLength"] == 8
        assert field.validation_rules["maxLength"] == 128
        assert "pattern" in field.validation_rules

    def test_schema_field_x_sup_metadata(self) -> None:
        """SchemaField with x-sup extension metadata."""
        field = SchemaField(
            field_id="event",
            field_type="object<Event>",
            metadata={
                "x-sup": {
                    "constraints": [
                        {
                            "requires": ["registrant"],
                            "status": {"allowed": ["validated"]},
                        }
                    ]
                }
            },
        )

        assert "x-sup" in field.metadata
        assert "constraints" in field.metadata["x-sup"]


# ============================================================================
# Test Schema Edge Cases
# ============================================================================


class TestSchemaEdgeCases:
    """Edge case tests for Schema."""

    def test_schema_with_special_characters_in_keys(self) -> None:
        """Schema with special characters in field keys."""
        fields = {
            "user-name": SchemaField(field_id="user-name"),
            "email_address": SchemaField(field_id="email_address"),
            "field.with.dots": SchemaField(field_id="field.with.dots"),
        }

        schema = Schema(root=fields)

        assert "user-name" in schema.root
        assert "email_address" in schema.root
        assert "field.with.dots" in schema.root

    def test_schema_large_number_of_fields(self) -> None:
        """Schema with large number of fields."""
        fields = {
            f"field_{i}": SchemaField(field_id=f"field_{i}", field_type="string")
            for i in range(100)
        }

        schema = Schema(root=fields)

        assert len(schema.root) == 100
        assert "field_0" in schema.root
        assert "field_99" in schema.root

    def test_schema_model_validate(self) -> None:
        """Schema should support model_validate for parsing."""
        data = {
            "name": {
                "field_id": "name",
                "field_type": "string",
                "label": "Name",
                "description": "",
                "required": True,
                "default_value": None,
                "validation_rules": {},
                "metadata": {},
            }
        }

        schema = Schema.model_validate(data)

        assert "name" in schema.root
        assert schema.root["name"].required is True
