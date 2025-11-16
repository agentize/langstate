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
    Info, ValueType, Field, Constraint, ValueTypeCondition,
    AllowDisallowCondition, RegexCondition, RangeCondition, Schema,
    PromptCondition, ValueSimilarityCondition, StatusCondition,
    Range, Pattern, Similarity, Prompt
)
from langstate.data_structure.dah import DirectedAcyclicHypergraphNode
from copy import deepcopy

# Constants for constraint relationship keys
# These are synonyms for specifying the source/prerequisite property in x-sup constraints
# Note: To avoid YAML 1.1 boolean coercion (e.g. on/off/yes/no), prefer using "source" or "from"
CONSTRAINT_SOURCE_KEYS = ["source", "from", "on", "prereq", "depends_on", "requires"]

# Constants for constraint target/dependency keys (used in top-level x-sup.constraints)
CONSTRAINT_TARGET_KEYS = ["to", "target", "dep", "dep_id", "dst"]


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
    
    # Configure YAML loader to preserve 'on', 'off', 'yes', 'no' as strings
    # instead of converting them to booleans (YAML 1.1 behavior)
    # This is critical for x-sup constraint keys like "on: registrant"
    class PreserveStringLoader(yaml.SafeLoader):
        pass
    
    # Remove boolean implicit resolver to prevent 'on'/'off'/'yes'/'no' conversion
    PreserveStringLoader.yaml_implicit_resolvers = {
        k: [r for r in v if r[0] != 'tag:yaml.org,2002:bool']
        for k, v in PreserveStringLoader.yaml_implicit_resolvers.copy().items()
    }
    
    # Load the YAML file (keep raw data to preserve x-sup extensions)
    try:
        with open(doc_path) as f:
            doc_data = yaml.load(f, Loader=PreserveStringLoader)
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

    # type -> ValueTypeCondition
    types = prop_schema.get("type")
    vt = _value_type_from_jsonschema(types)
    if vt:
        out.append(
            Constraint(
                conditions=[
                    ValueTypeCondition(
                        allowed=vt,
                        info=Info(name="type", description=f"Type constraint for {field_id}")
                    )
                ]
            )
        )

    # enum -> AllowDisallowCondition
    if "enum" in prop_schema and isinstance(prop_schema["enum"], list) and prop_schema["enum"]:
        out.append(
            Constraint(
                conditions=[
                    AllowDisallowCondition(
                        allowed=prop_schema["enum"],
                        info=Info(name="enumeration", description=f"Enumeration constraint for {field_id}")
                    )
                ]
            )
        )

    # pattern -> RegexCondition
    pattern = prop_schema.get("pattern")
    if pattern:
        out.append(
            Constraint(
                conditions=[
                    RegexCondition(
                        allowed=[Pattern(pattern=pattern)],
                        info=Info(name="regex", description=f"Regex constraint for {field_id}")
                    )
                ]
            )
        )

    # numeric range -> RangeCondition
    numeric_min = prop_schema.get("minimum")
    numeric_max = prop_schema.get("maximum")
    if numeric_min is not None or numeric_max is not None:
        out.append(
            Constraint(
                conditions=[
                    RangeCondition(
                        allowed=[Range(
                            min=float(numeric_min if numeric_min is not None else float("-inf")),
                            max=float(numeric_max if numeric_max is not None else float("+inf")),
                            inclusive_min=True,
                            inclusive_max=True
                        )],
                        info=Info(name="range", description=f"Range constraint for {field_id}")
                    )
                ]
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
                # For arrays, process nested items directly with the array field as prefix
                # e.g., "Registration.guests.email", "Registration.guests.name"
                # (the [*] notation is only used in visualization to indicate array items)
                nested_entity = f"{prop_name}_item".capitalize()
                nested_props = _get_properties_recursively(
                    nested_entity,
                    items,
                    api,
                    prefix=field_id,
                    visited=visited
                )
                result.update(nested_props)
    
    return result


def load_schema_from_openapi_yaml(
    doc: str | Path,
    root_entity: Optional[str] = None
) -> Schema:
    """
    Build Schema (DAH of Properties and Constraints) from OpenAPI YAML.
    
    This function reads an OpenAPI YAML file, validates it, and converts it to a Schema
    which is a DirectedAcyclicHypergraph[Property, Constraint]. Unlike the State loader which
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
    >>> # Visualize the schema
    >>> print(schema.to_ascii_tree())
    >>> print(schema.to_mermaid())
    """
    # 0) Convert doc to Path for later use
    doc_path = Path(doc) if isinstance(doc, str) else doc
    doc_path = doc_path.resolve()
    
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
    properties: Dict[str, Field] = {}
    for field_id, (prop_schema, entity_name) in all_properties.items():
        info = Info(
            name=field_id,
            description=prop_schema.get("description", "")
        )
        
        # Collect self-constraints from JSON Schema
        constraints = _mk_self_constraints(field_id, prop_schema)
        
        # Get default value
        default_value = prop_schema.get("default")
        
        properties[field_id] = Field(
            id=field_id,
            info=info,
            constraints=constraints,
            default_value=default_value,
            top_n=1,
            default_updaters=[],
            tags=[]
        )
    
    # 6) Create Property nodes (using Property.id as node ID)
    property_nodes: List[DirectedAcyclicHypergraphNode[Field, Constraint]] = []
    for field_id, property_obj in properties.items():
        property_nodes.append(
            DirectedAcyclicHypergraphNode[Field, Constraint](
                id=field_id,  # Use Property.id as node ID (not UUID)
                value=property_obj
            )
        )
    
    # 7) Create Schema DAG
    schema = Schema(nodes=property_nodes)
    
    # 8) Create structural hyperedges (parent property → child properties)
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
            # Create a 1-source hyperedge for structural relationship
            schema.add_hyperedge(
                sources=[parent_id],
                target_id=field_id,
                metadata=None,
                check_cycle=True,
            )
    
    # 9) Process x-sup.constraints to add extra constraint edges
    #    Constraints can be defined at:
    #    - property level: schema for a property has x-sup.constraints
    #    - array item level: items.x-sup.constraints or items.allOf[].x-sup.constraints
    #    - top-level: raw_doc.x-sup.constraints (optional)

    # Helper: retrieve x-sup from raw_doc by field path
    # This is needed because aiopenapi3 strips x-sup extensions when processing
    def _get_xsup_from_raw(field_id: str, raw_doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get x-sup extensions from raw_doc for a given field_id.
        
        Args:
            field_id: Field ID like "Registration.event" or "Registration.guests"
            raw_doc: Raw YAML document with x-sup preserved
        
        Returns:
            x-sup dict if found, None otherwise
        """
        # Parse field_id to navigate raw_doc
        # e.g., "Registration.event" → raw_doc['components']['schemas']['Registration']['properties']['event']
        parts = field_id.split(".")
        if not parts or parts[0] not in raw_doc.get("components", {}).get("schemas", {}):
            return None
        
        # Start from the root schema
        schema_name = parts[0]
        current = raw_doc["components"]["schemas"][schema_name]
        
        # Navigate through the path
        for i, part in enumerate(parts[1:], start=1):
            if not isinstance(current, dict):
                return None
            
            # Check if this is the last part - if so, look for x-sup here
            is_last = (i == len(parts) - 1)
            
            # Look in properties
            if "properties" in current and part in current["properties"]:
                current = current["properties"][part]
                if is_last and isinstance(current, dict):
                    return current.get("x-sup")
            # Look in items (for arrays)
            elif "items" in current:
                items = current["items"]
                # Check if items has allOf
                if isinstance(items, dict) and "allOf" in items:
                    # Search in allOf entries for properties or x-sup
                    for allof_item in items["allOf"]:
                        if not isinstance(allof_item, dict):
                            continue
                        # Check if this allOf item has the property we're looking for
                        if "properties" in allof_item and part in allof_item["properties"]:
                            current = allof_item["properties"][part]
                            if is_last and isinstance(current, dict):
                                return current.get("x-sup")
                            break
                        # Also check for x-sup on the items level (for array element constraints)
                        if is_last and "x-sup" in allof_item:
                            return allof_item.get("x-sup")
                elif isinstance(items, dict) and "properties" in items and part in items["properties"]:
                    current = items["properties"][part]
                    if is_last and isinstance(current, dict):
                        return current.get("x-sup")
                else:
                    return None
            else:
                return None
        
        return None

    # Helper: collect constraints declared on a property schema from raw_doc
    def _extract_constraints_for_property(field_id: str, raw_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract constraints from raw_doc for a given field_id.
        
        This looks up x-sup.constraints from the raw YAML document which preserves
        x-sup extensions (aiopenapi3 strips them during processing).
        """
        constraints_list: List[Dict[str, Any]] = []
        
        # Get x-sup from raw_doc
        x_sup = _get_xsup_from_raw(field_id, raw_doc)
        if x_sup and isinstance(x_sup, dict):
            items = x_sup.get("constraints", [])
            if isinstance(items, list):
                constraints_list.extend([c for c in items if isinstance(c, dict)])
        
        return constraints_list

    # Helper: normalize a constraint item into (prereq_id, dep_id, Constraint)
    # Note on YAML keys:
    # - We accept multiple synonyms for the prereq/source field defined in CONSTRAINT_SOURCE_KEYS.
    #   To avoid YAML 1.1 boolean coercion (e.g. on/off/yes/no), we recommend using "source" or "from".
    #   The YAML loader is already patched to preserve such keys as strings, but using "source" is
    #   clearer and more portable.
    def _normalize_constraint_item(dep_field_id: str, item: Dict[str, Any]) -> Optional[Tuple[List[str], str, Constraint]]:
        # Determine prereq/source key by checking all valid synonyms
        prereq_rel = None
        for key in CONSTRAINT_SOURCE_KEYS:
            if key in item:
                prereq_rel = item[key]
                break

        if prereq_rel is None:
            return None

        prereq_list: List[str] = []
        # Accept either a single string or a list of strings for sources
        if isinstance(prereq_rel, str):
            raw_sources = [prereq_rel]
        elif isinstance(prereq_rel, list):
            raw_sources = [x for x in prereq_rel if isinstance(x, str)]
            if not raw_sources:
                return None
        else:
            return None

        # Normalize absolute vs relative ids
        for rel in raw_sources:
            rel = rel.strip()
            if rel.startswith(f"{root_entity}."):
                prereq_list.append(rel)
            elif "." in rel:
                prereq_list.append(f"{root_entity}.{rel}")
            else:
                prereq_list.append(f"{root_entity}.{rel}")

        # Build metadata payload: support either a nested 'constraint' object or
        # top-level condition keys
        known_keys = {"property_type", "status", "regex", "enumeration", "range", "value_similarity", "prompt"}
        payload: Dict[str, Any] = {}
        if isinstance(item.get("constraint"), dict):
            payload = deepcopy(item["constraint"])  # type: ignore[index]
        else:
            for k in known_keys:
                if k in item:
                    payload[k] = item[k]

        # Build conditions list from payload
        conditions: List[Any] = []
        
        # property_type -> ValueTypeCondition
        if "property_type" in payload:
            pt = payload["property_type"]
            if isinstance(pt, dict):
                conditions.append(ValueTypeCondition(
                    info=Info(name="property_type", description="Property type constraint"),
                    **pt
                ))
            elif isinstance(pt, list):
                conditions.append(ValueTypeCondition(
                    allowed=pt,
                    info=Info(name="property_type", description="Property type constraint")
                ))
        
        # status -> StatusCondition
        if "status" in payload:
            st = payload["status"]
            if isinstance(st, dict):
                conditions.append(StatusCondition(
                    info=Info(name="status", description="Status constraint"),
                    **st
                ))
            elif isinstance(st, list):
                conditions.append(StatusCondition(
                    allowed=st,
                    info=Info(name="status", description="Status constraint")
                ))
        
        # regex -> RegexCondition
        if "regex" in payload:
            rx = payload["regex"]
            if isinstance(rx, str):
                conditions.append(RegexCondition(
                    allowed=[Pattern(pattern=rx)],
                    info=Info(name="regex", description="Regex constraint")
                ))
            elif isinstance(rx, dict):
                # Expect dict with 'pattern' key or full Pattern structure
                if 'pattern' in rx:
                    conditions.append(RegexCondition(
                        allowed=[Pattern(**rx)],
                        info=Info(name="regex", description="Regex constraint")
                    ))
                else:
                    # Assume it's allow/disallow structure with Pattern objects
                    conditions.append(RegexCondition(
                        info=Info(name="regex", description="Regex constraint"),
                        **rx
                    ))
        
        # enumeration -> AllowDisallowCondition
        if "enumeration" in payload:
            en = payload["enumeration"]
            if isinstance(en, list):
                conditions.append(AllowDisallowCondition(
                    allowed=en,
                    info=Info(name="enumeration", description="Enumeration constraint")
                ))
            elif isinstance(en, dict):
                conditions.append(AllowDisallowCondition(
                    info=Info(name="enumeration", description="Enumeration constraint"),
                    **en
                ))
        
        # range -> RangeCondition
        if "range" in payload:
            rg = payload["range"]
            if isinstance(rg, dict):
                # Check if it's a single Range definition or allow/disallow structure
                if 'min' in rg and 'max' in rg:
                    # Single range definition
                    conditions.append(RangeCondition(
                        allowed=[Range(**rg)],
                        info=Info(name="range", description="Range constraint")
                    ))
                else:
                    # Assume it's allow/disallow structure with Range objects
                    conditions.append(RangeCondition(
                        info=Info(name="range", description="Range constraint"),
                        **rg
                    ))
        
        # value_similarity -> ValueSimilarityCondition
        if "value_similarity" in payload:
            vs = payload["value_similarity"]
            if isinstance(vs, dict):
                # Check if it's a single Similarity definition or allow/disallow structure
                if 'reference' in vs and 'threshold' in vs:
                    # Single similarity definition
                    conditions.append(ValueSimilarityCondition(
                        allowed=[Similarity(**vs)],
                        info=Info(name="value_similarity", description="Value similarity constraint")
                    ))
                else:
                    # Assume it's allow/disallow structure with Similarity objects
                    conditions.append(ValueSimilarityCondition(
                        info=Info(name="value_similarity", description="Value similarity constraint"),
                        **vs
                    ))
        
        # prompt -> PromptCondition
        if "prompt" in payload:
            pr = payload["prompt"]
            if isinstance(pr, str):
                conditions.append(PromptCondition(
                    allowed=[Prompt(prompt=pr)],
                    info=Info(name="prompt", description="Prompt constraint")
                ))
            elif isinstance(pr, dict):
                # Check if it's a single Prompt definition or allow/disallow structure
                if 'prompt' in pr and len(pr) == 1:
                    # Single prompt definition
                    conditions.append(PromptCondition(
                        allowed=[Prompt(**pr)],
                        info=Info(name="prompt", description="Prompt constraint")
                    ))
                else:
                    # Assume it's allow/disallow structure with Prompt objects
                    conditions.append(PromptCondition(
                        info=Info(name="prompt", description="Prompt constraint"),
                        **pr
                    ))

        # Create Constraint with conditions
        # If no conditions found, return None
        if not conditions:
            return None
        
        try:
            constraint_meta = Constraint(conditions=conditions)
        except Exception:
            # Skip invalid constraint payloads gracefully
            return None

        return prereq_list, dep_field_id, constraint_meta

    # Collect constraints from each property schema and add edges
    for field_id, (prop_schema, _entity_name) in all_properties.items():
        c_items = _extract_constraints_for_property(field_id, raw_doc)
        if not c_items:
            continue
        for c in c_items:
            normalized = _normalize_constraint_item(field_id, c)
            if not normalized:
                continue
            source_ids, dep_id, meta = normalized

            # Only add if both nodes exist in the schema
            if dep_id in properties and all(s in properties for s in source_ids):
                schema.add_hyperedge(
                    sources=source_ids,
                    target_id=dep_id,
                    metadata=meta,
                    check_cycle=True,
                )
            # If prereq node not present (e.g., typo), skip silently

    # Also support optional top-level x-sup.constraints
    x_sup_root = raw_doc.get("x-sup", {}) if isinstance(raw_doc, dict) else {}
    root_constraints = []
    if isinstance(x_sup_root, dict):
        rc = x_sup_root.get("constraints", [])
        if isinstance(rc, list):
            root_constraints = [c for c in rc if isinstance(c, dict)]

    for c in root_constraints:
        # For top-level constraints, require explicit target key (or synonyms)
        dep_rel = None
        for key in CONSTRAINT_TARGET_KEYS:
            if key in c:
                dep_rel = c[key]
                break
        
        if not dep_rel or not isinstance(dep_rel, str):
            continue

        normalized = _normalize_constraint_item(dep_rel if dep_rel.startswith(f"{root_entity}.") else f"{root_entity}.{dep_rel}", c)
        if not normalized:
            continue
        source_ids, dep_id, meta = normalized
        # Ensure absolute dep_id
        if not dep_id.startswith(f"{root_entity}."):
            dep_id = f"{root_entity}.{dep_id}"
        if dep_id in properties and all(s in properties for s in source_ids):
            schema.add_hyperedge(sources=source_ids, target_id=dep_id, metadata=meta, check_cycle=True)

    return schema


# Convenience alias
load_schema = load_schema_from_openapi_yaml
