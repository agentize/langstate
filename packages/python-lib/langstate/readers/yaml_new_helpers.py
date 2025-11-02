"""
Additional helper functions and replacement for load_state_from_openapi_yaml

These should be added to yaml.py after the load_schema_from_openapi_yaml function
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional, Set
import yaml

def _resolve_ref(ref: str, spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Resolve a $ref pointer to the actual schema object."""
    if not ref.startswith("#/"):
        return None
    parts = ref[2:].split("/")
    current = spec
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _get_default_value(prop_schema: Dict[str, Any]) -> Optional[Any]:
    """Extract default value from property schema."""
    if "default" in prop_schema:
        return prop_schema["default"]
    
    # For objects and arrays, we don't set a default value
    prop_type = prop_schema.get("type")
    if prop_type == "object":
        return None
    elif prop_type == "array":
        return None
    
    return None


def _collect_properties_from_entity(
    entity_name: str,
    entity_schema: Dict[str, Any],
    spec: Dict[str, Any],
    visited: Set[str],
    prefix: str = "",
    _entity_properties_func=None,
    _resolve_ref_func=None
) -> Dict[str, Tuple[Dict[str, Any], str]]:
    """
    Recursively collect all properties from an entity and its nested objects.
    
    Returns:
        Dict mapping field_id -> (property_schema, entity_name)
    """
    if entity_name in visited:
        return {}
    visited.add(entity_name)
    
    result: Dict[str, Tuple[Dict[str, Any], str]] = {}
    props = _entity_properties_func(entity_schema)
    
    for prop_name, prop_schema in props.items():
        field_id = f"{prefix}{entity_name}.{prop_name}" if not prefix else f"{prefix}.{prop_name}"
        result[field_id] = (prop_schema, entity_name)
        
        # Handle object references ($ref)
        if "$ref" in prop_schema:
            ref_schema = _resolve_ref_func(prop_schema["$ref"], spec)
            if ref_schema:
                ref_entity = prop_schema["$ref"].split("/")[-1]
                nested = _collect_properties_from_entity(
                    ref_entity, ref_schema, spec, visited, prefix=field_id,
                    _entity_properties_func=_entity_properties_func,
                    _resolve_ref_func=_resolve_ref_func
                )
                result.update(nested)
        
        # Handle allOf with $ref
        for branch in prop_schema.get("allOf", []):
            if "$ref" in branch:
                ref_schema = _resolve_ref_func(branch["$ref"], spec)
                if ref_schema:
                    ref_entity = branch["$ref"].split("/")[-1]
                    nested = _collect_properties_from_entity(
                        ref_entity, ref_schema, spec, visited, prefix=field_id,
                        _entity_properties_func=_entity_properties_func,
                        _resolve_ref_func=_resolve_ref_func
                    )
                    result.update(nested)
        
        # Handle array items with $ref
        items_schema = prop_schema.get("items", {})
        if isinstance(items_schema, dict):
            # Handle direct $ref in items
            if "$ref" in items_schema:
                ref_schema = _resolve_ref_func(items_schema["$ref"], spec)
                if ref_schema:
                    ref_entity = items_schema["$ref"].split("/")[-1]
                    # For arrays, we create a template using [*] notation
                    nested = _collect_properties_from_entity(
                        ref_entity, ref_schema, spec, visited, prefix=f"{field_id}[*]",
                        _entity_properties_func=_entity_properties_func,
                        _resolve_ref_func=_resolve_ref_func
                    )
                    result.update(nested)
            
            # Handle allOf in items
            for branch in items_schema.get("allOf", []):
                if "$ref" in branch:
                    ref_schema = _resolve_ref_func(branch["$ref"], spec)
                    if ref_schema:
                        ref_entity = branch["$ref"].split("/")[-1]
                        nested = _collect_properties_from_entity(
                            ref_entity, ref_schema, spec, visited, prefix=f"{field_id}[*]",
                            _entity_properties_func=_entity_properties_func,
                            _resolve_ref_func=_resolve_ref_func
                        )
                        result.update(nested)
    
    return result
