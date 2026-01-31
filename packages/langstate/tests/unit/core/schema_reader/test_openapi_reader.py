"""
Comprehensive unit tests for OpenAPI Schema Reader implementation.

Tests cover:
- OpenAPI specification parsing (YAML and JSON)
- Schema field extraction
- Type determination (Integer, Number, String, Boolean, Array, Object, OneOf, AnyOf)
- Validation rules extraction
- x-sup metadata extraction
- Nested object handling
- Array items handling
- $ref resolution
- Error handling for invalid inputs

Target: 100% code coverage for schema_reader/openapi/reader.py
"""

# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false

from __future__ import annotations

import os
import tempfile
import pytest
from pathlib import Path
from typing import cast

from core.schema_reader.openapi.reader import OpenAPIReader
from core.schema_reader.base.schema import Schema


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_schema_path() -> Path:
    """Path to the sample registration schema."""
    return (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "schemas"
        / "registeration.yaml"
    )


@pytest.fixture
def openapi_reader() -> OpenAPIReader:
    """Create OpenAPI reader with Registration root entity."""
    return OpenAPIReader(root_entity="Registration")


@pytest.fixture
def temp_yaml_file() -> Path:
    """Create a temporary YAML file for testing."""
    content = """
openapi: 3.1.0
info:
  title: Test Schema
  version: 1.0.0
components:
  schemas:
    TestEntity:
      type: object
      properties:
        name:
          type: string
          description: Test name
          title: Name Field
        age:
          type: integer
          minimum: 0
          maximum: 150
      required:
        - name
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(content)
        return Path(f.name)


@pytest.fixture
def temp_json_file() -> Path:
    """Create a temporary JSON file for testing."""
    import json

    content = {
        "openapi": "3.1.0",
        "info": {"title": "Test Schema", "version": "1.0.0"},
        "components": {
            "schemas": {
                "TestEntity": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "value": {"type": "number", "format": "double"},
                    },
                }
            }
        },
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(content, f)
        return Path(f.name)


@pytest.fixture
def temp_unknown_ext_file() -> Path:
    """Create a temporary file with unknown extension (YAML content)."""
    content = """
openapi: 3.1.0
info:
  title: Test Schema
  version: 1.0.0
components:
  schemas:
    TestEntity:
      type: object
      properties:
        field:
          type: boolean
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        return Path(f.name)


@pytest.fixture
def temp_unknown_ext_json_file() -> Path:
    """Create a temporary file with unknown extension that will fail YAML parsing."""
    # Create content that will cause yaml.safe_load to fail by using tabs in a way that breaks YAML
    content = '{\t"openapi": "3.1.0", "info": {"title": "Test", "version": "1.0.0"}, "components": {"schemas": {"TestEntity": {"type": "object", "properties": {"data": {"type": "string"}}}}}}'
    with tempfile.NamedTemporaryFile(mode="w", suffix=".dat", delete=False) as f:
        f.write(content)
        return Path(f.name)


# ============================================================================
# Test OpenAPIReader Basic Functionality
# ============================================================================


class TestOpenAPIReaderInit:
    """Tests for OpenAPIReader initialization."""

    def test_init_with_root_entity(self) -> None:
        """OpenAPIReader should store root entity."""
        reader = OpenAPIReader(root_entity="Person")

        assert reader.root_entity == "Person"

    def test_init_with_different_entities(self) -> None:
        """OpenAPIReader should accept different root entities."""
        reader_event = OpenAPIReader(root_entity="Event")
        reader_guest = OpenAPIReader(root_entity="Guest")

        assert reader_event.root_entity == "Event"
        assert reader_guest.root_entity == "Guest"


# ============================================================================
# Test OpenAPIReader.read()
# ============================================================================


class TestOpenAPIReaderRead:
    """Tests for OpenAPIReader.read() method."""

    def test_read_registration_schema(
        self, openapi_reader: OpenAPIReader, sample_schema_path: Path
    ) -> None:
        """read() should parse registration schema correctly."""
        if not sample_schema_path.exists():
            pytest.skip(f"Sample schema not found: {sample_schema_path}")

        schema = openapi_reader.read(sample_schema_path)

        assert isinstance(schema, Schema)
        assert "id" in schema.root
        assert "registrant" in schema.root
        assert "event" in schema.root

    def test_read_with_string_path(
        self, openapi_reader: OpenAPIReader, sample_schema_path: Path
    ) -> None:
        """read() should accept string path."""
        if not sample_schema_path.exists():
            pytest.skip(f"Sample schema not found: {sample_schema_path}")

        schema = openapi_reader.read(str(sample_schema_path))

        assert isinstance(schema, Schema)

    def test_read_yaml_file(self, temp_yaml_file: Path) -> None:
        """read() should parse YAML files correctly."""
        reader = OpenAPIReader(root_entity="TestEntity")
        schema = reader.read(temp_yaml_file)

        assert isinstance(schema, Schema)
        assert "name" in schema.root
        assert "age" in schema.root
        assert schema.root["name"].required is True
        assert schema.root["age"].required is False

        # Cleanup
        os.unlink(temp_yaml_file)

    def test_read_json_file(self, temp_json_file: Path) -> None:
        """read() should parse JSON files correctly."""
        reader = OpenAPIReader(root_entity="TestEntity")
        schema = reader.read(temp_json_file)

        assert isinstance(schema, Schema)
        assert "id" in schema.root
        assert "value" in schema.root
        assert schema.root["value"].field_type == "number:double"

        # Cleanup
        os.unlink(temp_json_file)

    def test_read_unknown_extension_yaml_content(
        self, temp_unknown_ext_file: Path
    ) -> None:
        """read() should try YAML first for unknown extensions."""
        reader = OpenAPIReader(root_entity="TestEntity")
        schema = reader.read(temp_unknown_ext_file)

        assert isinstance(schema, Schema)
        assert "field" in schema.root
        assert schema.root["field"].field_type == "boolean"

        # Cleanup
        os.unlink(temp_unknown_ext_file)

    def test_read_unknown_extension_json_fallback(
        self, temp_unknown_ext_json_file: Path
    ) -> None:
        """read() should fall back to JSON when YAML fails."""
        reader = OpenAPIReader(root_entity="TestEntity")
        schema = reader.read(temp_unknown_ext_json_file)

        assert isinstance(schema, Schema)
        assert "data" in schema.root

        # Cleanup
        os.unlink(temp_unknown_ext_json_file)

    def test_read_file_not_found_raises(self) -> None:
        """read() should raise FileNotFoundError for missing files."""
        reader = OpenAPIReader(root_entity="Test")

        with pytest.raises(
            FileNotFoundError, match="OpenAPI specification file not found"
        ):
            reader.read("/nonexistent/path/schema.yaml")

    def test_read_root_entity_not_found_raises(self, temp_yaml_file: Path) -> None:
        """read() should raise ValueError if root entity not found."""
        reader = OpenAPIReader(root_entity="NonExistent")

        with pytest.raises(ValueError, match="Root entity 'NonExistent' not found"):
            reader.read(temp_yaml_file)

        # Cleanup
        os.unlink(temp_yaml_file)

    def test_read_no_root_entity_raises(self) -> None:
        """read() should raise ValueError if no root entity specified."""
        reader = OpenAPIReader(root_entity="")

        content = """
openapi: 3.1.0
info:
  title: Test
  version: 1.0.0
components:
  schemas:
    Test:
      type: object
      properties:
        field:
          type: string
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        with pytest.raises(ValueError, match="No root_entity specified"):
            reader.read(temp_path)

        # Cleanup
        os.unlink(temp_path)

    def test_read_no_components_raises(self) -> None:
        """read() should raise ValueError if no components/schemas found."""
        reader = OpenAPIReader(root_entity="Test")

        content = """
openapi: 3.1.0
info:
  title: Test
  version: 1.0.0
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        with pytest.raises(ValueError, match="No components/schemas found"):
            reader.read(temp_path)

        # Cleanup
        os.unlink(temp_path)

    def test_read_no_schemas_in_components_raises(self) -> None:
        """read() should raise ValueError if schemas missing in components."""
        reader = OpenAPIReader(root_entity="Test")

        content = """
openapi: 3.1.0
info:
  title: Test
  version: 1.0.0
components:
  parameters: {}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        with pytest.raises(ValueError, match="No components/schemas found"):
            reader.read(temp_path)

        # Cleanup
        os.unlink(temp_path)

    def test_read_with_path_object(self, temp_yaml_file: Path) -> None:
        """read() should accept Path object directly."""
        reader = OpenAPIReader(root_entity="TestEntity")
        schema = reader.read(temp_yaml_file)  # Already a Path

        assert isinstance(schema, Schema)

        # Cleanup
        os.unlink(temp_yaml_file)


# ============================================================================
# Test OpenAPIReader._determine_field_type()
# ============================================================================


class TestOpenAPIReaderDetermineFieldType:
    """Tests for field type determination."""

    def test_determine_field_type_integer(self) -> None:
        """_determine_field_type should handle integer type."""
        reader = OpenAPIReader(root_entity="Test")

        # Integer without format
        schema = {"type": "integer"}
        result = reader._determine_field_type(schema, {})
        assert result == "integer"

        # Integer with format
        schema = {"type": "integer", "format": "int64"}
        result = reader._determine_field_type(schema, {})
        assert result == "integer:int64"

    def test_determine_field_type_number(self) -> None:
        """_determine_field_type should handle number type."""
        reader = OpenAPIReader(root_entity="Test")

        # Number without format
        schema = {"type": "number"}
        result = reader._determine_field_type(schema, {})
        assert result == "number"

        # Number with format
        schema = {"type": "number", "format": "double"}
        result = reader._determine_field_type(schema, {})
        assert result == "number:double"

    def test_determine_field_type_string(self) -> None:
        """_determine_field_type should handle string type."""
        reader = OpenAPIReader(root_entity="Test")

        # String without format
        schema = {"type": "string"}
        result = reader._determine_field_type(schema, {})
        assert result == "string"

        # String with format
        schema = {"type": "string", "format": "email"}
        result = reader._determine_field_type(schema, {})
        assert result == "string:email"

    def test_determine_field_type_boolean(self) -> None:
        """_determine_field_type should handle boolean type."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"type": "boolean"}
        result = reader._determine_field_type(schema, {})
        assert result == "boolean"

    def test_determine_field_type_array_with_items(self) -> None:
        """_determine_field_type should handle array with items."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"type": "array", "items": {"type": "string"}}
        result = reader._determine_field_type(schema, {})
        assert result == "array<string>"

    def test_determine_field_type_array_without_items(self) -> None:
        """_determine_field_type should handle array without items."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"type": "array"}
        result = reader._determine_field_type(schema, {})
        assert result == "array"

    def test_determine_field_type_object(self) -> None:
        """_determine_field_type should handle object type."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"type": "object"}
        result = reader._determine_field_type(schema, {})
        assert result == "object"

    def test_determine_field_type_ref(self) -> None:
        """_determine_field_type should handle $ref."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"$ref": "#/components/schemas/Person"}
        result = reader._determine_field_type(schema, {})
        assert result == "object<Person>"

    def test_determine_field_type_oneof(self) -> None:
        """_determine_field_type should handle oneOf."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"oneOf": [{"type": "string"}, {"type": "integer"}]}
        result = reader._determine_field_type(schema, {})
        assert result == "oneOf<string,integer>"

    def test_determine_field_type_anyof(self) -> None:
        """_determine_field_type should handle anyOf."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"anyOf": [{"type": "boolean"}, {"type": "number"}]}
        result = reader._determine_field_type(schema, {})
        assert result == "anyOf<boolean,number>"

    def test_determine_field_type_unknown(self) -> None:
        """_determine_field_type should return 'unknown' for no type."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {}
        result = reader._determine_field_type(schema, {})
        assert result == "unknown"

    def test_determine_field_type_fallback(self) -> None:
        """_determine_field_type should fall back to type value."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"type": "custom_type"}
        result = reader._determine_field_type(schema, {})
        assert result == "custom_type"


# ============================================================================
# Test OpenAPIReader._extract_validation_rules()
# ============================================================================


class TestOpenAPIReaderExtractValidationRules:
    """Tests for validation rules extraction."""

    def test_extract_string_validations(self) -> None:
        """_extract_validation_rules should extract string validations."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {
            "type": "string",
            "minLength": 5,
            "maxLength": 100,
            "pattern": r"^[a-z]+$",
        }

        rules = reader._extract_validation_rules(schema)

        assert rules["minLength"] == 5
        assert rules["maxLength"] == 100
        assert rules["pattern"] == r"^[a-z]+$"

    def test_extract_string_validations_partial(self) -> None:
        """_extract_validation_rules should skip missing string validations."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"type": "string", "minLength": 1}

        rules = reader._extract_validation_rules(schema)

        assert rules["minLength"] == 1
        assert "maxLength" not in rules
        assert "pattern" not in rules

    def test_extract_number_validations(self) -> None:
        """_extract_validation_rules should extract number validations."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "exclusiveMinimum": True,
            "exclusiveMaximum": False,
        }

        rules = reader._extract_validation_rules(schema)

        assert rules["minimum"] == 0
        assert rules["maximum"] == 100
        assert rules["exclusiveMinimum"] is True
        assert rules["exclusiveMaximum"] is False

    def test_extract_integer_validations(self) -> None:
        """_extract_validation_rules should extract integer validations."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"type": "integer", "minimum": 1, "maximum": 500}

        rules = reader._extract_validation_rules(schema)

        assert rules["minimum"] == 1
        assert rules["maximum"] == 500
        assert "exclusiveMinimum" not in rules
        assert "exclusiveMaximum" not in rules

    def test_extract_array_validations(self) -> None:
        """_extract_validation_rules should extract array validations."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"type": "array", "minItems": 1, "maxItems": 49, "uniqueItems": True}

        rules = reader._extract_validation_rules(schema)

        assert rules["minItems"] == 1
        assert rules["maxItems"] == 49
        assert rules["uniqueItems"] is True

    def test_extract_array_validations_partial(self) -> None:
        """_extract_validation_rules should skip missing array validations."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"type": "array", "minItems": 0}

        rules = reader._extract_validation_rules(schema)

        assert rules["minItems"] == 0
        assert "maxItems" not in rules
        assert "uniqueItems" not in rules

    def test_extract_enum_validation(self) -> None:
        """_extract_validation_rules should extract enum values."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"type": "string", "enum": ["draft", "confirmed", "cancelled"]}

        rules = reader._extract_validation_rules(schema)

        assert rules["enum"] == ["draft", "confirmed", "cancelled"]

    def test_extract_no_validations(self) -> None:
        """_extract_validation_rules should return empty dict when no rules."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"type": "string"}

        rules = reader._extract_validation_rules(schema)

        assert rules == {}


# ============================================================================
# Test OpenAPIReader._parse_schema()
# ============================================================================


class TestOpenAPIReaderParseSchema:
    """Tests for schema parsing."""

    def test_parse_schema_non_object_returns_empty(self) -> None:
        """_parse_schema should return empty dict for non-object schemas."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"type": "string"}
        result = reader._parse_schema(schema, {})

        assert result == {}

    def test_parse_schema_no_properties_returns_empty(self) -> None:
        """_parse_schema should return empty dict for object without properties."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"type": "object"}
        result = reader._parse_schema(schema, {})

        assert result == {}

    def test_parse_schema_object_with_properties(self) -> None:
        """_parse_schema should parse object with properties."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Test description",
                    "title": "Test Title",
                }
            },
            "required": ["name"],
        }

        result = reader._parse_schema(schema, {})

        assert "name" in result
        assert result["name"].field_id == "name"
        assert result["name"].required is True
        assert result["name"].description == "Test description"
        assert result["name"].label == "Test Title"

    def test_parse_schema_with_default_label(self) -> None:
        """_parse_schema should generate label from field name."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {
            "type": "object",
            "properties": {"user_name": {"type": "string", "default": "default_value"}},
        }

        result = reader._parse_schema(schema, {})

        assert result["user_name"].label == "User Name"
        assert result["user_name"].default_value == "default_value"
        assert result["user_name"].required is False

    def test_parse_schema_with_x_sup_metadata(self) -> None:
        """_parse_schema should extract x-sup metadata."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {
            "type": "object",
            "properties": {
                "event": {
                    "type": "string",
                    "x-sup": {"constraints": [{"requires": ["user_id"]}]},
                }
            },
        }

        result = reader._parse_schema(schema, {})

        assert "x-sup" in result["event"].metadata
        x_sup_metadata = cast(
            "dict[str, list[dict[str, list[str]]]]", result["event"].metadata["x-sup"]
        )
        assert x_sup_metadata["constraints"][0]["requires"] == ["user_id"]

    def test_parse_schema_nested_object(self) -> None:
        """_parse_schema should recursively parse nested objects."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {
            "type": "object",
            "properties": {
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                    },
                }
            },
        }

        result = reader._parse_schema(schema, {})

        assert "address" in result
        assert isinstance(result["address"].default_value, dict)
        assert "street" in result["address"].default_value
        assert "city" in result["address"].default_value

    def test_parse_schema_with_ref_resolution(self) -> None:
        """_parse_schema should resolve $ref in schema."""
        reader = OpenAPIReader(root_entity="Test")

        all_schemas = {
            "Address": {"type": "object", "properties": {"city": {"type": "string"}}}
        }

        schema = {"$ref": "#/components/schemas/Address"}

        result = reader._parse_schema(schema, all_schemas)

        assert "city" in result

    def test_parse_schema_with_ref_not_found(self) -> None:
        """_parse_schema should handle $ref not found in all_schemas."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"$ref": "#/components/schemas/NonExistent"}

        result = reader._parse_schema(schema, {})

        assert result == {}

    def test_parse_schema_property_with_ref(self) -> None:
        """_parse_schema should resolve $ref in properties."""
        reader = OpenAPIReader(root_entity="Test")

        all_schemas = {"Name": {"type": "string", "description": "A name field"}}

        schema = {
            "type": "object",
            "properties": {"name": {"$ref": "#/components/schemas/Name"}},
        }

        result = reader._parse_schema(schema, all_schemas)

        assert "name" in result
        assert result["name"].field_type == "string"
        assert result["name"].description == "A name field"

    def test_parse_schema_property_ref_not_found(self) -> None:
        """_parse_schema should handle property $ref not found."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {
            "type": "object",
            "properties": {"field": {"$ref": "#/components/schemas/Missing"}},
        }

        result = reader._parse_schema(schema, {})

        assert "field" in result
        assert result["field"].field_type == "object<Missing>"

    def test_parse_schema_array_of_objects(self) -> None:
        """_parse_schema should handle arrays of objects."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {
            "type": "object",
            "properties": {
                "guests": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                    },
                }
            },
        }

        result = reader._parse_schema(schema, {})

        assert "guests" in result
        assert isinstance(result["guests"].default_value, dict)
        assert "name" in result["guests"].default_value

    def test_parse_schema_array_items_with_ref(self) -> None:
        """_parse_schema should resolve $ref in array items."""
        reader = OpenAPIReader(root_entity="Test")

        all_schemas = {
            "Guest": {
                "type": "object",
                "properties": {"email": {"type": "string", "format": "email"}},
            }
        }

        schema = {
            "type": "object",
            "properties": {
                "guests": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/Guest"},
                }
            },
        }

        result = reader._parse_schema(schema, all_schemas)

        assert "guests" in result
        assert isinstance(result["guests"].default_value, dict)
        assert "email" in result["guests"].default_value

    def test_parse_schema_array_items_ref_not_found(self) -> None:
        """_parse_schema should handle array items $ref not found."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/Missing"},
                }
            },
        }

        result = reader._parse_schema(schema, {})

        assert "items" in result
        # Items ref not resolved, so no default_value set
        assert result["items"].default_value is None

    def test_parse_schema_array_with_non_object_items(self) -> None:
        """_parse_schema should handle arrays with non-object items."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {
            "type": "object",
            "properties": {"tags": {"type": "array", "items": {"type": "string"}}},
        }

        result = reader._parse_schema(schema, {})

        assert "tags" in result
        assert result["tags"].default_value is None
        assert result["tags"].field_type == "array<string>"

    def test_parse_schema_empty_properties(self) -> None:
        """_parse_schema should handle object with empty properties."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"type": "object", "properties": {}}

        result = reader._parse_schema(schema, {})

        assert result == {}


# ============================================================================
# Test Integration with Real Schema
# ============================================================================


class TestOpenAPIReaderIntegration:
    """Integration tests with real schema file."""

    def test_read_full_registration_schema(self, sample_schema_path: Path) -> None:
        """read() should correctly parse full registration schema."""
        if not sample_schema_path.exists():
            pytest.skip(f"Sample schema not found: {sample_schema_path}")

        reader = OpenAPIReader(root_entity="Registration")
        schema = reader.read(sample_schema_path)

        # Check top-level fields
        assert "id" in schema.root
        assert "registrant" in schema.root
        assert "event" in schema.root
        assert "guests" in schema.root
        assert "total_price" in schema.root
        assert "status" in schema.root

        # Check field types
        assert "object" in schema.root["registrant"].field_type
        assert "object" in schema.root["event"].field_type
        assert "array" in schema.root["guests"].field_type

    def test_read_event_entity(self, sample_schema_path: Path) -> None:
        """read() should correctly parse Event entity."""
        if not sample_schema_path.exists():
            pytest.skip(f"Sample schema not found: {sample_schema_path}")

        reader = OpenAPIReader(root_entity="Event")
        schema = reader.read(sample_schema_path)

        assert "id" in schema.root
        assert "name" in schema.root
        assert "description" in schema.root
        assert "schedule" in schema.root
        assert "capacity" in schema.root
        assert "pricing" in schema.root

    def test_read_person_entity(self, sample_schema_path: Path) -> None:
        """read() should correctly parse Person entity."""
        if not sample_schema_path.exists():
            pytest.skip(f"Sample schema not found: {sample_schema_path}")

        reader = OpenAPIReader(root_entity="Person")
        schema = reader.read(sample_schema_path)

        assert "id" in schema.root
        assert "name" in schema.root
        assert "email" in schema.root


# ============================================================================
# Test Edge Cases and Coverage
# ============================================================================


class TestOpenAPIReaderEdgeCases:
    """Edge case tests for OpenAPIReader."""

    def test_read_with_yml_extension(self) -> None:
        """read() should handle .yml extension."""
        content = """
openapi: 3.1.0
info:
  title: Test
  version: 1.0.0
components:
  schemas:
    Test:
      type: object
      properties:
        field:
          type: string
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        reader = OpenAPIReader(root_entity="Test")
        schema = reader.read(temp_path)

        assert "field" in schema.root

        # Cleanup
        os.unlink(temp_path)

    def test_parse_schema_with_validation_rules(self) -> None:
        """_parse_schema should include validation rules in fields."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "format": "email",
                    "minLength": 5,
                    "maxLength": 255,
                }
            },
        }

        result = reader._parse_schema(schema, {})

        assert result["email"].validation_rules["minLength"] == 5
        assert result["email"].validation_rules["maxLength"] == 255

    def test_parse_schema_no_required_field(self) -> None:
        """_parse_schema should handle missing required array."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {
            "type": "object",
            "properties": {"optional_field": {"type": "string"}},
            # No 'required' key
        }

        result = reader._parse_schema(schema, {})

        assert result["optional_field"].required is False

    def test_parse_schema_no_description(self) -> None:
        """_parse_schema should handle missing description."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"type": "object", "properties": {"field": {"type": "integer"}}}

        result = reader._parse_schema(schema, {})

        assert result["field"].description == ""

    def test_determine_field_type_array_with_nested_ref(self) -> None:
        """_determine_field_type should handle arrays with $ref items."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"type": "array", "items": {"$ref": "#/components/schemas/Person"}}

        result = reader._determine_field_type(schema, {})

        assert result == "array<object<Person>>"

    def test_parse_schema_with_non_standard_ref(self) -> None:
        """_parse_schema should handle $ref that doesn't start with #/components/schemas/."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {"$ref": "#/definitions/SomeType"}

        # Should return empty since it can't resolve non-standard ref
        result = reader._parse_schema(schema, {})

        assert result == {}

    def test_parse_schema_property_with_non_standard_ref(self) -> None:
        """_parse_schema should handle property $ref that doesn't start with #/components/schemas/."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {
            "type": "object",
            "properties": {"field": {"$ref": "#/definitions/CustomType"}},
        }

        result = reader._parse_schema(schema, {})

        # Property should still be created but ref can't be resolved
        # Since _determine_field_type also checks for #/components/schemas/ prefix,
        # it won't extract the name and will return "unknown"
        assert "field" in result
        assert result["field"].field_type == "unknown"

    def test_parse_schema_array_items_with_non_standard_ref(self) -> None:
        """_parse_schema should handle array items $ref that doesn't start with #/components/schemas/."""
        reader = OpenAPIReader(root_entity="Test")

        schema = {
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": {"$ref": "#/definitions/Item"}}
            },
        }

        result = reader._parse_schema(schema, {})

        assert "items" in result
        # Since ref can't be resolved, default_value should be None
        assert result["items"].default_value is None

    def test_determine_field_type_with_non_standard_ref(self) -> None:
        """_determine_field_type should handle $ref that doesn't start with #/components/schemas/."""
        reader = OpenAPIReader(root_entity="Test")

        # Non-standard ref still extracts the name
        schema = {"$ref": "#/definitions/CustomType"}
        result = reader._determine_field_type(schema, {})

        # Since it doesn't start with #/components/schemas/, it falls through to normal handling
        # which won't find a type, so returns unknown
        assert result == "unknown"

    def test_complete_workflow(self) -> None:
        """Test complete workflow with all features."""
        content = """
openapi: 3.1.0
info:
  title: Complete Test
  version: 1.0.0
components:
  schemas:
    Address:
      type: object
      properties:
        street:
          type: string
        city:
          type: string
    
    Person:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
          minLength: 1
          maxLength: 100
        age:
          type: integer
          minimum: 0
          maximum: 150
        email:
          type: string
          format: email
        is_active:
          type: boolean
          default: true
        score:
          type: number
          format: float
          exclusiveMinimum: 0
          exclusiveMaximum: 100
        address:
          $ref: "#/components/schemas/Address"
        tags:
          type: array
          items:
            type: string
          minItems: 0
          maxItems: 10
          uniqueItems: true
        status:
          type: string
          enum: ["active", "inactive", "pending"]
        preference:
          oneOf:
            - type: string
            - type: integer
        option:
          anyOf:
            - type: boolean
            - type: number
        metadata:
          type: object
          properties:
            created_at:
              type: string
              format: date-time
        x-sup:
          custom: data
      required:
        - id
        - name
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        reader = OpenAPIReader(root_entity="Person")
        schema = reader.read(temp_path)

        # Verify all fields parsed
        assert "id" in schema.root
        assert "name" in schema.root
        assert "age" in schema.root
        assert "email" in schema.root
        assert "is_active" in schema.root
        assert "score" in schema.root
        assert "address" in schema.root
        assert "tags" in schema.root
        assert "status" in schema.root
        assert "preference" in schema.root
        assert "option" in schema.root
        assert "metadata" in schema.root

        # Check types
        assert schema.root["id"].field_type == "string:uuid"
        assert schema.root["age"].field_type == "integer"
        assert schema.root["email"].field_type == "string:email"
        assert schema.root["is_active"].field_type == "boolean"
        assert schema.root["score"].field_type == "number:float"
        # Note: $ref properties get their type resolved, so it shows object (not object<Address>)
        # because the property schema itself is resolved to the referenced schema
        assert schema.root["address"].field_type == "object"
        assert schema.root["tags"].field_type == "array<string>"
        assert schema.root["status"].field_type == "string"
        assert "oneOf" in schema.root["preference"].field_type
        assert "anyOf" in schema.root["option"].field_type
        assert schema.root["metadata"].field_type == "object"

        # Check required
        assert schema.root["id"].required is True
        assert schema.root["name"].required is True
        assert schema.root["age"].required is False

        # Check validations
        assert schema.root["name"].validation_rules["minLength"] == 1
        assert schema.root["name"].validation_rules["maxLength"] == 100
        assert schema.root["age"].validation_rules["minimum"] == 0
        assert schema.root["age"].validation_rules["maximum"] == 150
        assert schema.root["score"].validation_rules["exclusiveMinimum"] == 0
        assert schema.root["score"].validation_rules["exclusiveMaximum"] == 100
        assert schema.root["tags"].validation_rules["minItems"] == 0
        assert schema.root["tags"].validation_rules["maxItems"] == 10
        assert schema.root["tags"].validation_rules["uniqueItems"] is True
        assert schema.root["status"].validation_rules["enum"] == [
            "active",
            "inactive",
            "pending",
        ]

        # Check default value
        assert schema.root["is_active"].default_value is True

        # Check nested object parsing
        assert isinstance(schema.root["address"].default_value, dict)
        assert "street" in schema.root["address"].default_value
        assert isinstance(schema.root["metadata"].default_value, dict)
        assert "created_at" in schema.root["metadata"].default_value

        # Cleanup
        os.unlink(temp_path)
