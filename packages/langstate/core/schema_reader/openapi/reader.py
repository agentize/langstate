from pathlib import Path
from typing import Dict, Union, Any, cast

from openapi_parser import parse
from openapi_parser.specification import (
    Specification,
    Object as OpenAPIObject,
    Schema as OpenAPISchema,
    Integer,
    Number,
    String as OpenAPIString,
    Boolean,
    Array,
    OneOf,
    AnyOf,
)

from ..base.reader import BaseSchemaReader
from ..base.schema import Schema, SchemaField


class OpenAPIReader(BaseSchemaReader):
    """
    Reads and interprets OpenAPI specifications to extract API schema information.

    Uses openapi3-parser library to parse OpenAPI 3.x specifications in YAML or JSON format.
    Can extract schema from a specified root entity using x-sup.root_entity extension.
    """

    def __init__(self, root_entity: str):
        """Initialize OpenAPI reader.

        Args:
            root_entity: Optional entity name to use as root schema.
                        If not provided, will try to read from x-sup.root_entity.
        """
        self.root_entity = root_entity

    def read(self, source: Union[str, Path]) -> Schema:
        """Read and parse OpenAPI schema from the given source.

        Args:
            source: Schema source - can be a file path (str/Path) or dict

        Returns:
            Parsed Schema object

        Raises:
            ValueError: If the schema source is invalid
            FileNotFoundError: If the source file doesn't exist
        """
        # Parse OpenAPI specification using openapi3-parser
        specification: Specification = parse(str(source))

        # Determine root entity
        root_entity = self.root_entity
        if not root_entity:
            raise ValueError(
                "No root_entity specified. Provide it in constructor or x-sup.root_entity"
            )

        # Get the schema from components/schemas
        if root_entity not in specification.schemas:
            raise ValueError(
                f"Root entity '{root_entity}' not found in components/schemas"
            )

        root_schema = specification.schemas[root_entity]

        # Parse the schema
        fields = self._parse_schema(root_schema, specification.schemas)

        return Schema(root=fields)

    def _parse_schema(
        self, schema: OpenAPISchema, all_schemas: Dict[str, OpenAPISchema]
    ) -> Dict[str, SchemaField]:
        """Parse an OpenAPI schema into SchemaField dictionary.

        Args:
            schema: The OpenAPI schema object
            all_schemas: All available schemas for reference resolution

        Returns:
            Dictionary mapping field names to SchemaField objects
        """
        fields: Dict[str, SchemaField] = {}

        # Only Object schemas have properties
        if not isinstance(schema, OpenAPIObject):
            return fields

        # Parse each property
        for prop in schema.properties:
            field_type = self._determine_field_type(prop.schema, all_schemas)
            is_required = prop.name in schema.required

            # Extract metadata
            description = prop.schema.description or ""
            label = prop.schema.title or prop.name.replace("_", " ").title()

            # Extract validation rules
            validation_rules = self._extract_validation_rules(prop.schema)

            # Extract x-sup metadata if present
            metadata: Dict[str, Any] = {}
            extensions = getattr(prop.schema, "extensions", None)
            if isinstance(extensions, dict) and "x-sup" in extensions:
                # cast to Dict[str, Any] for the type checker before accessing by string key
                ext = cast(Dict[str, Any], extensions)
                metadata["x-sup"] = ext.get("x-sup")

            # Handle default value and nested fields
            default_value = prop.schema.default
            if isinstance(prop.schema, OpenAPIObject):
                # Recursively parse nested object fields and put them in default_value
                default_value = self._parse_schema(prop.schema, all_schemas)

            fields[prop.name] = SchemaField(
                field_id=prop.name,
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
        self, schema: OpenAPISchema, all_schemas: Dict[str, OpenAPISchema]
    ) -> str:
        """Determine the field type from schema.

        Args:
            schema: OpenAPI schema
            all_schemas: All available schemas

        Returns:
            Field type as string
        """
        # Handle specific schema types
        if isinstance(schema, Integer):
            field_type = "integer"
            if schema.format:
                field_type = f"integer:{schema.format.value}"
            return field_type

        if isinstance(schema, Number):
            field_type = "number"
            if schema.format:
                field_type = f"number:{schema.format.value}"
            return field_type

        if isinstance(schema, OpenAPIString):
            field_type = "string"
            if schema.format:
                field_type = f"string:{schema.format.value}"
            return field_type

        if isinstance(schema, Boolean):
            return "boolean"

        if isinstance(schema, Array):
            if schema.items:
                item_type = self._determine_field_type(schema.items, all_schemas)
                return f"array<{item_type}>"
            return "array"

        if isinstance(schema, OpenAPIObject):
            # Try to find the schema name
            for name, s in all_schemas.items():
                if s is schema:
                    return f"object<{name}>"
            return "object"

        if isinstance(schema, OneOf):
            if schema.schemas:
                types = [
                    self._determine_field_type(s, all_schemas) for s in schema.schemas
                ]
                return f"oneOf<{','.join(types)}>"
            return "oneOf"

        if isinstance(schema, AnyOf):
            if schema.schemas:
                types = [
                    self._determine_field_type(s, all_schemas) for s in schema.schemas
                ]
                return f"anyOf<{','.join(types)}>"
            return "anyOf"

        # Fallback to basic type
        return schema.type.value if hasattr(schema, "type") else "unknown"

    def _extract_validation_rules(self, schema: OpenAPISchema) -> Dict[str, Any]:
        """Extract validation rules from schema.

        Args:
            schema: OpenAPI schema

        Returns:
            Dictionary of validation rules
        """
        rules: Dict[str, Any] = {}

        # String validations
        if isinstance(schema, OpenAPIString):
            if schema.min_length is not None:
                rules["minLength"] = schema.min_length
            if schema.max_length is not None:
                rules["maxLength"] = schema.max_length
            if schema.pattern:
                rules["pattern"] = schema.pattern

        # Number validations
        if isinstance(schema, (Integer, Number)):
            if schema.minimum is not None:
                rules["minimum"] = schema.minimum
            if schema.maximum is not None:
                rules["maximum"] = schema.maximum
            if schema.exclusive_minimum is not None:
                rules["exclusiveMinimum"] = schema.exclusive_minimum
            if schema.exclusive_maximum is not None:
                rules["exclusiveMaximum"] = schema.exclusive_maximum

        # Array validations
        if isinstance(schema, Array):
            if schema.min_items is not None:
                rules["minItems"] = schema.min_items
            if schema.max_items is not None:
                rules["maxItems"] = schema.max_items
            if schema.unique_items is not None:
                rules["uniqueItems"] = schema.unique_items

        # Enum
        if hasattr(schema, "enum") and schema.enum:
            rules["enum"] = schema.enum

        return rules
