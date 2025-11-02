"""
OpenAPI YAML to Schema converter.

This module reads OpenAPI YAML files with x-sup extensions and converts them to
a Schema (DirectedAcyclicGraph[Property, Constraint]).

Unlike yaml_simplified.py which creates State (PropertyInstances with UUIDs),
this creates Schema (Property definitions with their constraint relationships).
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
from aiopenapi3 import OpenAPI, FileSystemLoader
from langstate.models import (
    Info, ValueType, Property, Constraint, PropertyTypeCondition, 
    EnumerationCondition, RegexCondition, RangeCondition, Schema
)
from langstate.data_structure.dag import DirectedAcyclicGraphNode


def _load_and_validate_openapi(doc: str | Path) -> Tuple[OpenAPI, Dict[str, Any]]:
    """Load and validate OpenAPI 3.1 spec using aiopenapi3.
    
    Args:
        doc: Path to OpenAPI YAML file
    
    Returns:
        Tuple of (api, raw_doc_data) where raw_doc_data preserves x-sup extensions
        
    Raises:
        ValueError: If the YAML is not valid OpenAPI 3.1
    """
    import copy
    
    # Convert to Path if string
    doc_path = Path(doc) if isinstance(doc, str) else doc
    doc_path = doc_path.resolve()
    
    if not doc_path.exists():
        raise FileNotFoundError(f"File not found: {doc_path}")
    
    # Load the YAML file (keep raw data to preserve x-sup extensions)
    try:
        with open(doc_path) as f:
            doc_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML file: {e}")
    
    # Validate OpenAPI version
    openapi_version = doc_data.get("openapi", "")
    if not openapi_version.startswith("3."):
        raise ValueError(f"Unsupported OpenAPI version: {openapi_version}. Only OpenAPI 3.x is supported.")
    
    # Make a deep copy to preserve original x-sup extensions
    # (OpenAPI constructor modifies the dict)
    raw_doc = copy.deepcopy(doc_data)
    
    # Create OpenAPI instance with FileSystemLoader for proper $ref resolution
    try:
        loader = FileSystemLoader(doc_path.parent)
        api = OpenAPI(url=str(doc_path), document=doc_data, loader=loader)
    except Exception as e:
        raise ValueError(f"Invalid OpenAPI specification: {e}")
    
    # Validate that we have components.schemas
    if not api.components or not api.components.schemas:
        raise ValueError("OpenAPI spec must contain components.schemas")
    
    return api, raw_doc


def _schema_to_dict(schema_obj: Any) -> Dict[str, Any]:
    """Convert aiopenapi3 schema object to dict for processing."""
    if isinstance(schema_obj, dict):
        return schema_obj
    if hasattr(schema_obj, 'model_dump'):
        return schema_obj.model_dump()
    if hasattr(schema_obj, '__dict__'):
        return vars(schema_obj)
    return dict(schema_obj)


def _value_type_from_jsonschema(t: str | List[str]) -> List[ValueType]:
    """Convert JSON Schema type to ValueType enum."""
    if isinstance(t, list):
        types = t
    else:
        types = [t] if t else []
    
    out: List[ValueType] = []
    for x in types:
        if x == "string":
            out.append(ValueType.STRING)
        elif x == "integer":
            out.append(ValueType.INTEGER)
        elif x == "number":
            out.append(ValueType.NUMBER)
        elif x == "boolean":
            out.append(ValueType.BOOLEAN)
        elif x == "object":
            out.append(ValueType.REFERENCE)
        elif x == "array":
            out.append(ValueType.ARRAY)
    return out


def _mk_self_constraints(field_id: str, prop_schema: Dict[str, Any]) -> List[Constraint]:
    """Translate JSON Schema facets into self constraints."""
    out: List[Constraint] = []

    # type -> PropertyTypeCondition
    types = prop_schema.get("type")
    vt = _value_type_from_jsonschema(types)
    if vt:
        out.append(
            Constraint(
                property_type=PropertyTypeCondition(allowed=vt)
            )
        )

    # enum -> EnumerationCondition
    if "enum" in prop_schema and isinstance(prop_schema["enum"], list) and prop_schema["enum"]:
        out.append(
            Constraint(
                enumeration=EnumerationCondition(values=prop_schema["enum"])
            )
        )

    # pattern -> RegexCondition
    pattern = prop_schema.get("pattern")
    if pattern:
        out.append(
            Constraint(
                regex=RegexCondition(pattern=pattern)
            )
        )

    # numeric range -> RangeCondition
    numeric_min = prop_schema.get("minimum")
    numeric_max = prop_schema.get("maximum")
    if numeric_min is not None or numeric_max is not None:
        out.append(
            Constraint(
                range=RangeCondition(
                    min=float(numeric_min if numeric_min is not None else float("-inf")),
                    max=float(numeric_max if numeric_max is not None else float("+inf")),
                    inclusive_min=True,
                    inclusive_max=True,
                )
            )
        )

    return out


def _get_properties_recursively(
    entity_name: str,
    schema: Dict[str, Any] | Any,
    api: 'OpenAPI',
    prefix: str = "",
    visited: Optional[Set[str]] = None
) -> Dict[str, Tuple[Dict[str, Any], str]]:
    """
    Recursively collect all properties from a schema, resolving $refs via API.
    
    Args:
        entity_name: Name of the current entity being processed
        schema: Schema dict or object to process
        api: OpenAPI instance for resolving $refs
        prefix: Current property path prefix
        visited: Set of visited schema names to prevent cycles
    
    Returns:
        Dict mapping field_id -> (property_schema, entity_name)
    """
    if visited is None:
        visited = set()
    
    # Prevent infinite recursion on entity level
    visit_key = f"{prefix}.{entity_name}"
    if visit_key in visited:
        return {}
    visited.add(visit_key)
    
    result: Dict[str, Tuple[Dict[str, Any], str]] = {}
    
    # Convert schema to dict if needed
    schema_dict = _schema_to_dict(schema) if not isinstance(schema, dict) else schema
    
    # Handle allOf at schema level (merge properties from all schemas)
    properties = {}
    if hasattr(schema, 'allOf') and schema.allOf:
        # Schema object with allOf - merge properties from all sub-schemas
        for sub_schema in schema.allOf:
            if hasattr(sub_schema, 'properties') and sub_schema.properties:
                # Add properties from this sub-schema
                for prop_name, prop_obj in sub_schema.properties.items():
                    properties[prop_name] = prop_obj
    else:
        # Get properties from schema dict
        properties = schema_dict.get("properties", {})
    
    for prop_name, prop_schema_raw in properties.items():
        # Convert prop_schema to dict if needed
        prop_schema = _schema_to_dict(prop_schema_raw) if not isinstance(prop_schema_raw, dict) else prop_schema_raw
        
        # Build field ID
        if prefix:
            field_id = f"{prefix}.{prop_name}"
        else:
            field_id = f"{entity_name}.{prop_name}"
        
        # Resolve $ref if present (aiopenapi3 uses "ref" without $ in serialized dicts)
        if "ref" in prop_schema and prop_schema["ref"]:
            ref_path = prop_schema["ref"]
            if ref_path.startswith("#/components/schemas/"):
                schema_name = ref_path.split("/")[-1]
                if schema_name in api.components.schemas:
                    # Get the referenced schema
                    ref_schema_obj = api.components.schemas[schema_name]
                    ref_schema_dict = _schema_to_dict(ref_schema_obj)
                    
                    # Merge the resolved schema with current prop_schema (keeping x-sup if present)
                    # prop_schema might have x-sup, ref_schema_dict has the actual properties
                    merged_schema = {**ref_schema_dict, **prop_schema}
                    prop_schema = merged_schema
                    
                    # Recursively process referenced schema's properties
                    if "properties" in ref_schema_dict:
                        nested_props = _get_properties_recursively(
                            schema_name,
                            ref_schema_dict,
                            api,
                            prefix=field_id,
                            visited=visited
                        )
                        result.update(nested_props)
        
        # Add this property
        result[field_id] = (prop_schema, entity_name)
        
        # Handle nested objects (type: object with properties)
        if prop_schema.get("type") == "object" and "properties" in prop_schema:
            nested_entity = prop_name.capitalize()
            nested_props = _get_properties_recursively(
                nested_entity,
                prop_schema,
                api,
                prefix=field_id,
                visited=visited
            )
            result.update(nested_props)
        
        # Handle arrays of objects
        if prop_schema.get("type") == "array":
            items = prop_schema.get("items", {})
            
            # Handle allOf in items (common pattern in OpenAPI)
            # Look at the raw allOf array to find the $ref (aiopenapi3 uses "ref" without $)
            if isinstance(items, dict) and "allOf" in items:
                allof_list = items.get("allOf", [])
                if isinstance(allof_list, list):
                    for sub_schema in allof_list:
                        sub_dict = _schema_to_dict(sub_schema) if not isinstance(sub_schema, dict) else sub_schema
                        if "ref" in sub_dict and sub_dict["ref"]:
                            ref_path = sub_dict["ref"]
                            if ref_path.startswith("#/components/schemas/"):
                                schema_name = ref_path.split("/")[-1]
                                if schema_name in api.components.schemas:
                                    # Use the referenced schema directly
                                    ref_schema_obj = api.components.schemas[schema_name]
                                    items = ref_schema_obj  # Use object, not dict
                                    break
            
            # Check if items has properties (recursively process array item schema)
            items_has_props = False
            if hasattr(items, 'properties'):
                items_has_props = bool(items.properties)
            elif isinstance(items, dict):
                items_has_props = bool(items.get("properties"))
            
            if items and (items.get("type") == "object" if isinstance(items, dict) else True) or items_has_props:
                nested_entity = f"{prop_name}_item".capitalize()
                nested_props = _get_properties_recursively(
                    nested_entity,
                    items,
                    api,
                    prefix=f"{field_id}[*]",
                    visited=visited
                )
                result.update(nested_props)
    
    return result


def load_schema_from_openapi_yaml(
    doc: str | Path,
    root_entity: Optional[str] = None
) -> Schema:
    """
    Build Schema (DAG of Properties and Constraints) from OpenAPI YAML.
    
    This function reads an OpenAPI YAML file, validates it, and converts it to a Schema
    which is a DirectedAcyclicGraph[Property, Constraint]. Unlike the State loader which
    creates PropertyInstances with UUIDs, this creates the Property definitions themselves.
    
    Parameters
    ----------
    doc : str or Path
        Path to the OpenAPI YAML file
    root_entity : Optional[str]
        Root entity name from x-sup.root_entity. If not provided, will look for it in x-sup
    
    Returns
    -------
    Schema : A Schema DAG with Property nodes and Constraint edges
    
    Raises
    ------
    FileNotFoundError : If the YAML file doesn't exist
    ValueError : If the YAML is invalid or not valid OpenAPI 3.x
    
    Examples
    --------
    >>> schema = load_schema_from_openapi_yaml('api.yaml')
    >>> print(f'Schema has {len(schema.nodes)} properties')
    >>> # Access a specific property
    >>> registration_id = schema.nodes['Registration.id']
    >>> print(registration_id.value.info.description)
    """
    # 1) Load and validate OpenAPI spec
    api, raw_doc = _load_and_validate_openapi(doc)
    
    # 2) Get root entity from x-sup extensions or parameter
    if root_entity is None:
        x_sup = raw_doc.get("x-sup", {})
        root_entity = x_sup.get("root_entity")
    
    if not root_entity:
        raise ValueError("root_entity not specified. Either provide it as a parameter or include x-sup.root_entity in the YAML")
    
    # 3) Validate root entity exists in schemas
    if root_entity not in api.components.schemas:
        available = ", ".join(api.components.schemas.keys())
        raise ValueError(f"Root entity '{root_entity}' not found in components.schemas. Available: {available}")
    
    # Get the schema object and convert to dict for processing
    root_schema_obj = api.components.schemas[root_entity]
    root_schema = _schema_to_dict(root_schema_obj)
    
    # 4) Collect all properties recursively with proper $ref resolution
    all_properties = _get_properties_recursively(root_entity, root_schema, api)
    
    if not all_properties:
        raise ValueError(f"No properties found in root entity '{root_entity}'")
    
    # 5) Create Property objects for each field
    properties: Dict[str, Property] = {}
    for field_id, (prop_schema, entity_name) in all_properties.items():
        info = Info(
            name=field_id,
            description=prop_schema.get("description", "")
        )
        
        # Collect self-constraints from JSON Schema
        constraints = _mk_self_constraints(field_id, prop_schema)
        
        # Get default value
        default_value = prop_schema.get("default")
        
        properties[field_id] = Property(
            id=field_id,
            info=info,
            constraints=constraints,
            default_value=default_value,
            top_n=1,
            default_updaters=[],
            tags=[]
        )
    
    # 6) Create Property nodes (using Property.id as node ID)
    property_nodes: List[DirectedAcyclicGraphNode[Property, Constraint]] = []
    for field_id, property_obj in properties.items():
        property_nodes.append(
            DirectedAcyclicGraphNode[Property, Constraint](
                id=field_id,  # Use Property.id as node ID (not UUID)
                value=property_obj
            )
        )
    
    # 7) Create Schema DAG
    schema = Schema(nodes=property_nodes)
    
    # 8) Create structural edges (parent property → child properties)
    # These represent the containment/composition relationships in the schema
    for field_id in all_properties.keys():
        parts = field_id.split(".")
        
        # Skip root-level properties (no parent)
        if len(parts) <= 1:
            continue
        
        # Handle array notation [*]
        if "[*]" in field_id:
            # e.g., "Registration.guests[*].name" → parent is "Registration.guests[*]"
            parent_parts = []
            for part in parts[:-1]:
                parent_parts.append(part)
            parent_id = ".".join(parent_parts)
        else:
            # e.g., "Registration.event.name" → parent is "Registration.event"
            parent_id = ".".join(parts[:-1])
        
        # Create edge if parent exists
        if parent_id in properties and field_id in properties:
            # For Schema, we can add constraint edges if needed
            # For now, just create structural edges without explicit constraints
            # The parent-child relationship itself is the constraint
            schema.add_edge(
                prereq_id=parent_id,
                dep_id=field_id,
                metadata=None,  # Schema edges don't need constraint metadata
                check_cycle=True
            )
    
    return schema


# Convenience alias
load_schema = load_schema_from_openapi_yaml
