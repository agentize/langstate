"""Readers module for loading schemas from various sources.

This module provides schema reader implementations for various formats:
- OpenAPIYamlReader: Reads OpenAPI YAML files with x-sup extensions
"""

from typing import Any, Dict, Union
from pathlib import Path

from langstate.core.langstate import BaseSchemaReader
from langstate.models.field import Schema


class OpenAPIYamlReader(BaseSchemaReader):
    """Schema reader for OpenAPI YAML files with x-sup extensions.

    This reader loads OpenAPI 3.x YAML specifications and converts them
    to LangState Schema objects.

    Example:
        reader = OpenAPIYamlReader()
        schema = reader.read("./schema.yaml")
    """

    def read(self, source: Union[str, Path, Dict[str, Any]]) -> Schema:
        """Read and parse schema from OpenAPI YAML file.

        Args:
            source: Path to YAML file or dict containing schema

        Returns:
            Parsed Schema object

        Raises:
            ValueError: If the schema source is invalid
            FileNotFoundError: If the source file doesn't exist
        """
        from .yaml import load_schema_from_openapi_yaml

        return load_schema_from_openapi_yaml(source)


__all__ = [
    "OpenAPIYamlReader",
]
