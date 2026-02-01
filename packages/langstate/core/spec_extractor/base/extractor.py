"""Spec Extractor interface for LangState.

The Spec Extractor is responsible for:
- Loading and parsing schema definitions from various sources (YAML, JSON, OpenAPI, etc.)
- Converting to internal Schema representation
- Validating schema structure
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

from .schema import Schema


class BaseSpecExtractor(ABC):
    """Abstract base class for spec extractors.

    Spec extractors are responsible for loading and parsing schema definitions
    from various sources (YAML, JSON, OpenAPI specs, etc.).

    Example implementation:
        class OpenAPIYamlExtractor(BaseSpecExtractor):
            def read(self, source: Union[str, Path, Dict[str, object]]) -> Schema:
                # Load YAML file
                if isinstance(source, (str, Path)):
                    with open(source) as f:
                        data = yaml.safe_load(f)
                else:
                    data = source

                # Parse OpenAPI schema - build {key: SchemaField} dict
                fields = {}
                for prop_name, prop_def in data.get("properties", {}).items():
                    fields[prop_name] = SchemaField(
                        field_id=prop_name,
                        field_type=prop_def.get("type", "string"),
                        label=prop_def.get("title", prop_name),
                        description=prop_def.get("description", ""),
                        required=prop_name in data.get("required", [])
                    )

                # Schema is now a simple {key: SchemaField} mapping
                return Schema(__root__=fields)
    """

    @abstractmethod
    def read(self, source: Union[str, Path]) -> Schema:
        """Read and parse schema from the given source.

        Args:
            source: Schema source - can be a file path (str/Path) or dict

        Returns:
            Parsed Schema object

        Raises:
            ValueError: If the schema source is invalid
            FileNotFoundError: If the source file doesn't exist
        """
        pass
