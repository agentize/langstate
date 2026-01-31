from pathlib import Path
from typing import Dict, Union, Any

import yaml
import json

from ..base.extractor import BaseSpecExtractor
from ..base.schema import Schema, SchemaField


class OpenAPIReader(BaseSpecExtractor):
    """
    Reads and interprets OpenAPI specifications to extract API schema information.

    Parses OpenAPI 3.x specifications in YAML or JSON format.
    Can extract schema from a specified root entity using x-sup.root_entity extension.
    """

    def __init__(self, root_entity: str):
        """Initialize OpenAPI reader.

        Args:
            root_entity: Entity name to use as root schema.
        """
        self.root_entity = root_entity

    def read(self, source: Union[str, Path]) -> Schema:
        """Read and parse OpenAPI schema from the given source.

        Args:
            source: Schema source - can be a file path (str/Path)

        Returns:
            Parsed Schema object

        Raises:
            ValueError: If the schema source is invalid
            FileNotFoundError: If the source file doesn't exist
        """
        # Load the OpenAPI specification
        source_path = Path(source) if not isinstance(source, Path) else source

        if not source_path.exists():
            raise FileNotFoundError(f"OpenAPI specification file not found: {source}")

        # Parse the file based on extension
        with open(source_path, "r", encoding="utf-8") as f:
            if source_path.suffix in [".yaml", ".yml"]:
                spec_dict = yaml.safe_load(f)
            elif source_path.suffix == ".json":
                spec_dict = json.load(f)
            else:
                # Try YAML first, then JSON
                content = f.read()
                try:
                    spec_dict = yaml.safe_load(content)
                except yaml.YAMLError:
                    spec_dict = json.loads(content)

        # Determine root entity
        root_entity = self.root_entity
        if not root_entity:
            raise ValueError("No root_entity specified. Provide it in constructor")

        # Get the schema from components/schemas
        if "components" not in spec_dict or "schemas" not in spec_dict["components"]:
            raise ValueError("No components/schemas found in OpenAPI specification")

        schemas = spec_dict["components"]["schemas"]

        if root_entity not in schemas:
            raise ValueError(
                f"Root entity '{root_entity}' not found in components/schemas"
            )

        root_schema = schemas[root_entity]

        # Parse the schema
        fields = self._parse_schema(root_schema, schemas)

        return Schema(root=fields)

    def _parse_schema(
        self, schema: Dict[str, Any], all_schemas: Dict[str, Dict[str, Any]]
    ) -> Dict[str, SchemaField]:
        """Parse an OpenAPI schema into SchemaField dictionary.

        Args:
            schema: The OpenAPI schema dictionary
            all_schemas: All available schemas for reference resolution

        Returns:
            Dictionary mapping field names to SchemaField objects
        """
        fields: Dict[str, SchemaField] = {}

        # Resolve $ref if present
        if "$ref" in schema:
            ref_path = schema["$ref"]
            if ref_path.startswith("#/components/schemas/"):
                schema_name = ref_path.split("/")[-1]
                if schema_name in all_schemas:
                    schema = all_schemas[schema_name]

        # Only Object schemas have properties
        if schema.get("type") != "object" or "properties" not in schema:
            return fields

        properties = schema["properties"]
        required_fields = schema.get("required", [])

        # Parse each property
        for prop_name, prop_schema in properties.items():
            # Resolve $ref in property
            if "$ref" in prop_schema:
                ref_path = prop_schema["$ref"]
                if ref_path.startswith("#/components/schemas/"):
                    schema_name = ref_path.split("/")[-1]
                    if schema_name in all_schemas:
                        prop_schema = all_schemas[schema_name]

            field_type = self._determine_field_type(prop_schema, all_schemas)
            is_required = prop_name in required_fields

            # Extract metadata
            description = prop_schema.get("description", "")
            label = prop_schema.get("title", prop_name.replace("_", " ").title())

            # Extract validation rules
            validation_rules = self._extract_validation_rules(prop_schema)

            # Extract x-sup metadata if present
            metadata: Dict[str, Any] = {}
            if "x-sup" in prop_schema:
                metadata["x-sup"] = prop_schema["x-sup"]

            # Handle default value and nested fields
            default_value = prop_schema.get("default")

            if prop_schema.get("type") == "object":
                # Recursively parse nested object fields and put them in default_value
                default_value = self._parse_schema(prop_schema, all_schemas)
            elif prop_schema.get("type") == "array" and "items" in prop_schema:
                # Handle arrays of objects - parse the item schema
                items_schema = prop_schema["items"]
                if "$ref" in items_schema:
                    ref_path = items_schema["$ref"]
                    if ref_path.startswith("#/components/schemas/"):
                        schema_name = ref_path.split("/")[-1]
                        if schema_name in all_schemas:
                            items_schema = all_schemas[schema_name]

                if items_schema.get("type") == "object":
                    # Store the parsed item schema in default_value for array of objects
                    default_value = self._parse_schema(items_schema, all_schemas)

            fields[prop_name] = SchemaField(
                field_id=prop_name,
                field_type=field_type,
                label=label,
                description=description,
                required=is_required,
                default_value=default_value,
                validation_rules=validation_rules,
                metadata=metadata,
            )

        return fields

    def _determine_field_type(
        self, schema: Dict[str, Any], all_schemas: Dict[str, Dict[str, Any]]
    ) -> str:
        """Determine the field type from schema.

        Args:
            schema: OpenAPI schema dictionary
            all_schemas: All available schemas

        Returns:
            Field type as string
        """
        # Resolve $ref if present
        if "$ref" in schema:
            ref_path = schema["$ref"]
            if ref_path.startswith("#/components/schemas/"):
                schema_name = ref_path.split("/")[-1]
                return f"object<{schema_name}>"

        schema_type = schema.get("type")
        schema_format = schema.get("format")

        # Handle specific schema types
        if schema_type == "integer":
            if schema_format:
                return f"integer:{schema_format}"
            return "integer"

        if schema_type == "number":
            if schema_format:
                return f"number:{schema_format}"
            return "number"

        if schema_type == "string":
            if schema_format:
                return f"string:{schema_format}"
            return "string"

        if schema_type == "boolean":
            return "boolean"

        if schema_type == "array":
            if "items" in schema:
                item_type = self._determine_field_type(schema["items"], all_schemas)
                return f"array<{item_type}>"
            return "array"

        if schema_type == "object":
            return "object"

        # Handle oneOf
        if "oneOf" in schema:
            types = [
                self._determine_field_type(s, all_schemas) for s in schema["oneOf"]
            ]
            return f"oneOf<{','.join(types)}>"

        # Handle anyOf
        if "anyOf" in schema:
            types = [
                self._determine_field_type(s, all_schemas) for s in schema["anyOf"]
            ]
            return f"anyOf<{','.join(types)}>"

        # Fallback to basic type
        return schema_type if schema_type else "unknown"

    def _extract_validation_rules(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract validation rules from schema.

        Args:
            schema: OpenAPI schema dictionary

        Returns:
            Dictionary of validation rules
        """
        rules: Dict[str, Any] = {}

        schema_type = schema.get("type")

        # String validations
        if schema_type == "string":
            if "minLength" in schema:
                rules["minLength"] = schema["minLength"]
            if "maxLength" in schema:
                rules["maxLength"] = schema["maxLength"]
            if "pattern" in schema:
                rules["pattern"] = schema["pattern"]

        # Number validations
        if schema_type in ("integer", "number"):
            if "minimum" in schema:
                rules["minimum"] = schema["minimum"]
            if "maximum" in schema:
                rules["maximum"] = schema["maximum"]
            if "exclusiveMinimum" in schema:
                rules["exclusiveMinimum"] = schema["exclusiveMinimum"]
            if "exclusiveMaximum" in schema:
                rules["exclusiveMaximum"] = schema["exclusiveMaximum"]

        # Array validations
        if schema_type == "array":
            if "minItems" in schema:
                rules["minItems"] = schema["minItems"]
            if "maxItems" in schema:
                rules["maxItems"] = schema["maxItems"]
            if "uniqueItems" in schema:
                rules["uniqueItems"] = schema["uniqueItems"]

        # Enum
        if "enum" in schema:
            rules["enum"] = schema["enum"]

        return rules
