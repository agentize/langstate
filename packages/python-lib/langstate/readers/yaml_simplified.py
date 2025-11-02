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
            
            # Check if items has properties (recursively process Guest schema)
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
    
    # 3) Collect all properties recursively with proper $ref resolution
    all_properties = _get_properties_recursively(root_entity_name, root_schema, api)
    
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
    
    # 5) Create PropertyInstance nodes with initial snapshots and UUID IDs
    import uuid
    fv = initial_values or {}
    instance_nodes: List[DirectedAcyclicGraphNode[PropertyInstance, ConstraintInstance]] = []
    instances: Dict[str, PropertyInstance] = {}  # Map Property.id → PropertyInstance
    property_id_to_instance_id: Dict[str, str] = {}  # Map Property.id → PropertyInstance.id (UUID)
    
    for field_id, property_obj in properties.items():
        # Get value from initial_values or use default
        value = fv.get(field_id, property_obj.default_value)
        
        # Generate UUID for PropertyInstance
        instance_id = str(uuid.uuid4())
        
        # Create initial snapshot
        snapshots: List[PropertySnapshot] = [
            PropertySnapshot(
                id=f"{instance_id}@t0",
                status=PropertyStatusEnum.UNTOUCHED,
                value_confidences=[ValueConfidence(value=value, score=1.0)] if value is not None else [],
                updater=None,
                meta_data={}
            )
        ]
        
        property_instance = PropertyInstance(
            id=instance_id,  # UUID, not Property.id
            property=property_obj,
            snapshots=snapshots
        )
        instances[field_id] = property_instance  # Still keyed by Property.id for lookup
        property_id_to_instance_id[field_id] = instance_id
        instance_nodes.append(
            DirectedAcyclicGraphNode[PropertyInstance, ConstraintInstance](
                id=instance_id,  # Use UUID as node ID
                value=property_instance
            )
        )
    
    # 6) Create State DAG
    state = State(nodes=instance_nodes)
    
    # 6.5) Create automatic structural edges (parent object → child properties with status:generated)
    for field_id in all_properties.keys():
        parts = field_id.split(".")
        
        # Skip root-level properties (no parent)
        if len(parts) <= 2:  # e.g., "Registration.id" has no parent property
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
        if parent_id in instances and field_id in instances:
            parent_instance_id = property_id_to_instance_id[parent_id]
            child_instance_id = property_id_to_instance_id[field_id]
            
            # Create structural constraint (property is generated when parent is generated)
            structural_constraint = Constraint(
                status=PropertyStatusCondition(
                    allowed=[PropertyStatusEnum.GENERATED]
                )
            )
            
            constraint_inst = ConstraintInstance(
                id=f"structural:{parent_instance_id}→{child_instance_id}",
                constraints=[structural_constraint],
                confidence=1.0  # Structural edges have full confidence
            )
            
            state.add_edge(
                prereq_id=parent_instance_id,
                dep_id=child_instance_id,
                metadata=constraint_inst
            )
    
    # 7) Parse x-sup constraints and create edges
    # Collect all field_ids to check for x-sup (including array items like guests[*])
    field_ids_to_check = set(all_properties.keys())
    
    # Also check for array item x-sup (e.g., Registration.guests[*])
    for field_id in list(all_properties.keys()):
        if "[*]" in field_id:
            # Extract array path: "Registration.guests[*].id" → "Registration.guests[*]"
            parts = field_id.split(".")
            array_parts = []
            for part in parts:
                array_parts.append(part)
                if "[*]" in part:
                    break
            array_item_path = ".".join(array_parts)
            field_ids_to_check.add(array_item_path)
    
    for field_id in field_ids_to_check:
        # Get x-sup from raw schemas to preserve extensions
        x_sup_field = _get_raw_property_xsup(field_id, root_entity_name, raw_schemas)
        constraints_list = x_sup_field.get("constraints", [])
        
        for constraint_def in constraints_list:
            # Check if this references another property
            # Note: YAML parses "on:" as boolean True, so check both keys
            on_field = constraint_def.get("on") or constraint_def.get(True)
            if on_field:
                # Resolve relative references (Property IDs)
                if "." not in on_field:
                    parent_path = ".".join(field_id.split(".")[:-1])
                    prereq_property_id = f"{parent_path}.{on_field}" if parent_path else f"{root_entity_name}.{on_field}"
                else:
                    prereq_property_id = on_field
                
                # Create constraint edge if prerequisite exists (using PropertyInstance UUIDs)
                # Handle array items: if field_id ends with [*], apply constraint to all child properties
                target_fields = []
                if field_id.endswith("[*]"):
                    # Apply to all properties under this array item
                    for prop_id in all_properties.keys():
                        if prop_id.startswith(field_id + "."):
                            target_fields.append(prop_id)
                    # Also include the array itself if it exists
                    if field_id in instances:
                        target_fields.append(field_id)
                else:
                    target_fields = [field_id]
                
                for target_field in target_fields:
                    if prereq_property_id in instances and target_field in instances:
                        prereq_instance_id = property_id_to_instance_id[prereq_property_id]
                        dep_instance_id = property_id_to_instance_id[target_field]
                        
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
                                id=f"xsup:{prereq_instance_id}→{dep_instance_id}",
                                constraints=[status_constraint],
                                confidence=default_confidence
                            )
                            state.add_edge(
                                prereq_id=prereq_instance_id,  # Use UUID
                                dep_id=dep_instance_id,  # Use UUID
                                metadata=constraint_inst
                            )
    
    # 8) Print JSON representation of the state graph
    import json
    json_dict = state.to_json_dict()
    
    # Create a mapping of instance UUID to property ID for readable edges
    uuid_to_property = {}
    for n in json_dict["nodes"]:
        if n["value"] and isinstance(n["value"], dict) and "property" in n["value"]:
            uuid_to_property[n["id"]] = n["value"]["property"]["id"]
    
    # Create a simplified version for console output (without full value objects)
    simplified = {
        "node_count": json_dict["node_count"],
        "edge_count": json_dict["edge_count"],
        "nodes": [
            {
                "id": n["id"],
                "property_id": n["value"]["property"]["id"] if n["value"] and isinstance(n["value"], dict) and "property" in n["value"] else None
            }
            for n in json_dict["nodes"]
        ],
        "edges": [
            {
                "from": e["from"],
                "from_property": uuid_to_property.get(e["from"]),
                "to": e["to"],
                "to_property": uuid_to_property.get(e["to"]),
                "constraint_id": e["metadata"]["id"] if e["metadata"] and isinstance(e["metadata"], dict) and "id" in e["metadata"] else None,
                "type": "structural" if (e["metadata"] and isinstance(e["metadata"], dict) and e["metadata"].get("id", "").startswith("structural:")) else "xsup"
            }
            for e in json_dict["edges"]
        ]
    }
    
    print("\n" + "="*80)
    print("STATE GRAPH LOADED - JSON")
    print("="*80)
    print(json.dumps(simplified, indent=2))
    print("="*80 + "\n")
    
    # Print ASCII tree view
    def node_label_ascii(prop_instance):
        """Extract property ID as node label for ASCII tree."""
        if hasattr(prop_instance, 'property') and hasattr(prop_instance.property, 'id'):
            return prop_instance.property.id
        return str(prop_instance)
    
    # Find all root nodes (nodes with no prerequisites)
    root_node_ids = []
    for node_id, node in state.nodes.items():
        if not node.prerequisites():
            root_node_ids.append(node_id)
    
    print("="*80)
    print(f"STATE GRAPH LOADED - ASCII TREE ({len(root_node_ids)} root nodes)")
    print("="*80)
    if root_node_ids:
        ascii_tree = state.to_ascii_tree(root_nodes=root_node_ids, node_label_fn=node_label_ascii, max_depth=4)
        print(ascii_tree)
    else:
        print("(No root nodes found - possible cycle)")
    print("="*80 + "\n")
    
    # 9) Generate Mermaid diagram and save to Markdown
    def node_label(prop_instance):
        """Extract property ID as node label."""
        if hasattr(prop_instance, 'property') and hasattr(prop_instance.property, 'id'):
            return prop_instance.property.id
        return str(prop_instance)
    
    def edge_label(constraint_inst):
        """Extract constraint type as edge label."""
        if hasattr(constraint_inst, 'id'):
            if constraint_inst.id.startswith('structural:'):
                return 'structural'
            elif constraint_inst.id.startswith('xsup:'):
                # Try to extract status info
                if hasattr(constraint_inst, 'constraints') and constraint_inst.constraints:
                    first_constraint = constraint_inst.constraints[0]
                    if hasattr(first_constraint, 'status') and first_constraint.status:
                        status = first_constraint.status.allowed[0] if first_constraint.status.allowed else 'xsup'
                        return f'xsup:{status}'
                return 'xsup'
        return ''
    
    mermaid_diagram = state.to_mermaid(node_label_fn=node_label, edge_label_fn=edge_label, max_label_length=50)
    
    # Save to markdown file
    doc_path = Path(doc) if isinstance(doc, str) else doc
    output_path = doc_path.parent / f"{doc_path.stem}_diagram.md"
    
    markdown_content = f"""# State Graph Diagram: {root_entity_name}

Generated from: `{doc_path.name}`

## Statistics
- **Nodes**: {len(state.nodes)} PropertyInstances
- **Edges**: {sum(len(n.depends_on) for n in state.nodes.values())} ConstraintInstances
  - Structural edges: {sum(1 for n in state.nodes.values() for e in n.depends_on.values() if e.metadata and e.metadata.id.startswith('structural:'))}
  - X-sup edges: {sum(1 for n in state.nodes.values() for e in n.depends_on.values() if e.metadata and e.metadata.id.startswith('xsup:'))}

## Diagram

```mermaid
{mermaid_diagram}
```

## Legend

- **Structural edges**: Parent → Child property relationships (auto-generated)
- **X-sup edges**: Explicit constraint dependencies from x-sup extensions
- **Node labels**: Property IDs (e.g., `Registration.event.name`)

## Notes

This diagram shows the dependency graph where:
- Each node is a PropertyInstance with a unique UUID
- Edges represent ConstraintInstances (dependencies)
- Arrow direction: prerequisite → dependent
"""
    
    with open(output_path, 'w') as f:
        f.write(markdown_content)
    
    print(f"📊 Mermaid diagram saved to: {output_path}")
    print(f"   Open in VS Code or GitHub to view the rendered diagram\n")
    
    return state


# Keep backward compatibility
def load_state_from_openapi_yaml(
    doc: str | Path,
    initial_values: Optional[Dict[str, Any]] = None,
    default_confidence: float = 0.0,
) -> State:
    """Wrapper that uses the simplified v2 implementation if prance is available."""
    return load_state_from_openapi_yaml_v2(doc, initial_values, default_confidence)
