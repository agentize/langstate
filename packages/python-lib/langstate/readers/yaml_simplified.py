"""
Simplified OpenAPI YAML reader using aiopenapi3 for OpenAPI 3.1 support.

This approach leverages the aiopenapi3 library to handle all the complex
$ref resolution, schema merging, and OpenAPI 3.1 spec parsing automatically.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
from aiopenapi3 import OpenAPI, FileSystemLoader
from langstate.models import (
    Info, ValueType, Property, PropertyInstance, PropertySnapshot, 
    ValueConfidence, Constraint, PropertyTypeCondition, EnumerationCondition, 
    RegexCondition, RangeCondition, PropertyStatusCondition, PromptCondition, 
    ConstraintInstance, State, PropertyStatusEnum
)
from langstate.data_structure.dag import DirectedAcyclicGraphNode


def _load_and_resolve_openapi(doc: str | Path) -> Tuple[OpenAPI, Dict[str, Any]]:
    """Load OpenAPI 3.1 spec and resolve all $refs automatically using aiopenapi3.
    
    Returns:
        Tuple of (api, raw_doc_data) where raw_doc_data preserves x-sup extensions
    """
    import copy
    
    # Convert to Path if string
    doc_path = Path(doc) if isinstance(doc, str) else doc
    doc_path = doc_path.resolve()
    
    # Load the YAML file (keep raw data to preserve x-sup extensions)
    with open(doc_path) as f:
        doc_data = yaml.safe_load(f)
    
    # Make a deep copy to preserve original x-sup extensions
    # (OpenAPI constructor modifies the dict)
    raw_doc = copy.deepcopy(doc_data)
    
    # Create OpenAPI instance with FileSystemLoader for proper $ref resolution
    loader = FileSystemLoader(doc_path.parent)
    api = OpenAPI(url=str(doc_path), document=doc_data, loader=loader)
    
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


def _get_raw_property_xsup(
    field_id: str,
    root_entity_name: str,
    raw_schemas: Dict[str, Any]
) -> Dict[str, Any]:
    """Get x-sup extensions for a property from raw schema data.
    
    Args:
        field_id: e.g. "Registration.event" or "Registration.guests[*].invitation"
        root_entity_name: e.g. "Registration"
        raw_schemas: Raw schemas dict from YAML
    
    Returns:
        x-sup dict for the property, or {}
    """
    # Parse field_id to navigate raw schema
    parts = field_id.split(".")
    if not parts or parts[0] != root_entity_name:
        return {}
    
    # Start with root entity schema
    current_schema = raw_schemas.get(root_entity_name, {})
    
    # Navigate through nested properties
    for i, part in enumerate(parts[1:], 1):
        # Handle array notation [*]
        if part.endswith("[*]"):
            part = part[:-3]  # Remove [*]
            prop_schema = current_schema.get("properties", {}).get(part, {})
            # Get items schema for array
            current_schema = prop_schema.get("items", {})
            # Handle allOf
            if "allOf" in current_schema:
                for sub_schema in current_schema["allOf"]:
                    if "x-sup" in sub_schema:
                        return sub_schema.get("x-sup", {})
                    if "$ref" not in sub_schema:
                        current_schema = sub_schema
                        break
        else:
            # Regular property access
            prop_schema = current_schema.get("properties", {}).get(part, {})
            
            # If this is the last part, check for x-sup here
            if i == len(parts) - 1:
                return prop_schema.get("x-sup", {})
            
            # For nested navigation, resolve $ref if present
            if "$ref" in prop_schema:
                ref_path = prop_schema["$ref"]
                if ref_path.startswith("#/components/schemas/"):
                    schema_name = ref_path.split("/")[-1]
                    current_schema = raw_schemas.get(schema_name, {})
            elif "type" in prop_schema and prop_schema["type"] == "object":
                current_schema = prop_schema
            else:
                return {}
    
    return {}


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

    # numeric range -> RangeCondition (use 'range' instead of 'value_range')
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
    prefix: str = "",
    visited: Optional[Set[str]] = None
) -> Dict[str, Tuple[Dict[str, Any], str]]:
    """
    Recursively collect all properties from a schema.
    
    With aiopenapi3, all $refs are already resolved, so we just need to traverse
    the nested structure directly without manual $ref resolution.
    
    Returns:
        Dict mapping field_id -> (property_schema, entity_name)
    """
    if visited is None:
        visited = set()
    
    # Prevent infinite recursion
    visit_key = f"{prefix}.{entity_name}"
    if visit_key in visited:
        return {}
    visited.add(visit_key)
    
    result: Dict[str, Tuple[Dict[str, Any], str]] = {}
    
    # Convert schema to dict if needed
    schema_dict = _schema_to_dict(schema) if not isinstance(schema, dict) else schema
    
    # Get properties from this schema
    properties = schema_dict.get("properties", {})
    
    for prop_name, prop_schema_raw in properties.items():
        # Convert prop_schema to dict if needed
        prop_schema = _schema_to_dict(prop_schema_raw) if not isinstance(prop_schema_raw, dict) else prop_schema_raw
        
        # Build field ID
        if prefix:
            field_id = f"{prefix}.{prop_name}"
        else:
            field_id = f"{entity_name}.{prop_name}"
        
        # Add this property
        result[field_id] = (prop_schema, entity_name)
        
        # Handle nested objects (type: object with properties)
        if prop_schema.get("type") == "object" and "properties" in prop_schema:
            nested_entity = prop_name.capitalize()
            nested_props = _get_properties_recursively(
                nested_entity,
                prop_schema,
                prefix=field_id,
                visited=visited
            )
            result.update(nested_props)
        
        # Handle arrays of objects
        if prop_schema.get("type") == "array":
            items = prop_schema.get("items", {})
            if items and items.get("type") == "object":
                nested_entity = f"{prop_name}_item".capitalize()
                nested_props = _get_properties_recursively(
                    nested_entity,
                    items,
                    prefix=f"{field_id}[*]",
                    visited=visited
                )
                result.update(nested_props)
    
    return result


def load_state_from_openapi_yaml_v2(
    doc: str | Path,
    initial_values: Optional[Dict[str, Any]] = None,
    default_confidence: float = 0.0,
) -> State:
    """
    Build State DAG from OpenAPI YAML with x-sup extensions.
    
    This version uses prance for automatic $ref resolution, making the code
    much simpler and more reliable.
    
    Parameters
    ----------
    doc : path or YAML string
    initial_values : optional mapping of field_id -> value
    default_confidence : initial confidence for all constraint instances (0.0..1.0)
    
    Returns
    -------
    State : A State DAG with PropertyInstance nodes and ConstraintInstance edges
    """
    # Load and resolve all $refs automatically
    api, raw_doc = _load_and_resolve_openapi(doc)
    
    # 1) Get root entity from x-sup extensions (use raw doc to preserve x-sup)
    x_sup = raw_doc.get("x-sup", {})
    root_entity_name = x_sup.get("root_entity")
    if not root_entity_name:
        raise ValueError("x-sup.root_entity not found in OpenAPI spec")
    
    # 2) Get the root entity schema (already resolved by aiopenapi3)
    if not api.components or not api.components.schemas:
        raise ValueError("No schemas found in OpenAPI spec")
    
    if root_entity_name not in api.components.schemas:
        raise ValueError(f"Root entity '{root_entity_name}' not found in components.schemas")
    
    # Get the schema object and convert to dict for processing
    root_schema_obj = api.components.schemas[root_entity_name]
    root_schema = _schema_to_dict(root_schema_obj)
    
    # Keep raw schemas dict for x-sup extension access
    raw_schemas = raw_doc.get("components", {}).get("schemas", {})
    
    # 3) Collect all properties recursively (no manual $ref resolution needed!)
    all_properties = _get_properties_recursively(root_entity_name, root_schema)
    
    # 4) Create Property objects for each field
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
    
    # 5) Create PropertyInstance nodes with initial snapshots
    fv = initial_values or {}
    instance_nodes: List[DirectedAcyclicGraphNode[PropertyInstance, ConstraintInstance]] = []
    instances: Dict[str, PropertyInstance] = {}
    
    for field_id, property_obj in properties.items():
        # Get value from initial_values or use default
        value = fv.get(field_id, property_obj.default_value)
        
        # Create initial snapshot
        snapshots: List[PropertySnapshot] = [
            PropertySnapshot(
                id=f"{field_id}@t0",
                status=PropertyStatusEnum.UNTOUCHED,
                value_confidences=[ValueConfidence(value=value, score=1.0)] if value is not None else [],
                updater=None,
                meta_data={}
            )
        ]
        
        property_instance = PropertyInstance(
            id=field_id,
            property=property_obj,
            snapshots=snapshots
        )
        instances[field_id] = property_instance
        instance_nodes.append(
            DirectedAcyclicGraphNode[PropertyInstance, ConstraintInstance](
                id=property_instance.id,
                value=property_instance
            )
        )
    
    # 6) Create State DAG
    state = State(nodes=instance_nodes)
    
    # 7) Parse x-sup constraints and create edges
    for field_id, (prop_schema, entity_name) in all_properties.items():
        # Get x-sup from raw schemas to preserve extensions
        x_sup_field = _get_raw_property_xsup(field_id, root_entity_name, raw_schemas)
        constraints_list = x_sup_field.get("constraints", [])
        
        for constraint_def in constraints_list:
            # Check if this references another property
            on_field = constraint_def.get("on")
            if on_field:
                # Resolve relative references
                if "." not in on_field:
                    parent_path = ".".join(field_id.split(".")[:-1])
                    prereq_id = f"{parent_path}.{on_field}" if parent_path else f"{root_entity_name}.{on_field}"
                else:
                    prereq_id = on_field
                
                # Create constraint edge if prerequisite exists
                if prereq_id in instances:
                    # Parse status condition if present
                    status_def = constraint_def.get("status", {})
                    status_constraint = None
                    if status_def:
                        status_constraint = Constraint(
                            status=PropertyStatusCondition(
                                allowed=status_def.get("allowed", []),
                                disallowed=status_def.get("disallowed", [])
                            )
                        )
                    
                    # Parse prompt if present
                    prompt_text = constraint_def.get("prompt")
                    if prompt_text and status_constraint:
                        status_constraint = Constraint(
                            status=status_constraint.status,
                            prompt=PromptCondition(prompt=prompt_text)
                        )
                    
                    if status_constraint:
                        constraint_inst = ConstraintInstance(
                            id=f"{prereq_id}=>{field_id}",
                            constraints=[status_constraint],
                            confidence=default_confidence
                        )
                        state.add_edge(
                            prereq_id=prereq_id,
                            dep_id=field_id,
                            metadata=constraint_inst
                        )
    
    return state


# Keep backward compatibility
def load_state_from_openapi_yaml(
    doc: str | Path,
    initial_values: Optional[Dict[str, Any]] = None,
    default_confidence: float = 0.0,
) -> State:
    """Wrapper that uses the simplified v2 implementation if prance is available."""
    return load_state_from_openapi_yaml_v2(doc, initial_values, default_confidence)
