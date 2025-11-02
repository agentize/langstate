#!/usr/bin/env python3
"""Script to update yaml.py with new State loading function"""

import re

# Read the original file
with open("langstate/readers/yaml.py", "r") as f:
    content = f.read()

# 1. Update imports
old_import = """from langstate.models import Info, ValueType, Property, PropertyInstance, PropertySnapshot, ValueConfidence, Constraint, PropertyTypeCondition, EnumerationCondition, RegexCondition, ValueRangeCondition, PropertyStatusCondition, PromptCondition, PropertyDependencyInstance"""

new_import = """from langstate.models import Info, ValueType, Property, PropertyInstance, PropertySnapshot, ValueConfidence, Constraint, PropertyTypeCondition, EnumerationCondition, RegexCondition, ValueRangeCondition, PropertyStatusCondition, PromptCondition, ConstraintInstance, State, PropertyStatusEnum"""

content = content.replace(old_import, new_import)

# Update typing import
content = content.replace(
    "from typing import Any, Dict, List, Tuple, Optional",
    "from typing import Any, Dict, List, Tuple, Optional, Set"
)

# 2. Add helper functions before load_state_from_openapi_yaml
helper_functions = '''

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
    prefix: str = ""
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
    props = _entity_properties(entity_schema)
    
    for prop_name, prop_schema in props.items():
        field_id = f"{prefix}{entity_name}.{prop_name}" if not prefix else f"{prefix}.{prop_name}"
        result[field_id] = (prop_schema, entity_name)
        
        # Handle object references ($ref)
        if "$ref" in prop_schema:
            ref_schema = _resolve_ref(prop_schema["$ref"], spec)
            if ref_schema:
                ref_entity = prop_schema["$ref"].split("/")[-1]
                nested = _collect_properties_from_entity(
                    ref_entity, ref_schema, spec, visited, prefix=field_id
                )
                result.update(nested)
        
        # Handle allOf with $ref
        for branch in prop_schema.get("allOf", []):
            if "$ref" in branch:
                ref_schema = _resolve_ref(branch["$ref"], spec)
                if ref_schema:
                    ref_entity = branch["$ref"].split("/")[-1]
                    nested = _collect_properties_from_entity(
                        ref_entity, ref_schema, spec, visited, prefix=field_id
                    )
                    result.update(nested)
        
        # Handle array items with $ref
        items_schema = prop_schema.get("items", {})
        if isinstance(items_schema, dict):
            # Handle direct $ref in items
            if "$ref" in items_schema:
                ref_schema = _resolve_ref(items_schema["$ref"], spec)
                if ref_schema:
                    ref_entity = items_schema["$ref"].split("/")[-1]
                    # For arrays, we create a template using [*] notation
                    nested = _collect_properties_from_entity(
                        ref_entity, ref_schema, spec, visited, prefix=f"{field_id}[*]"
                    )
                    result.update(nested)
            
            # Handle allOf in items
            for branch in items_schema.get("allOf", []):
                if "$ref" in branch:
                    ref_schema = _resolve_ref(branch["$ref"], spec)
                    if ref_schema:
                        ref_entity = branch["$ref"].split("/")[-1]
                        nested = _collect_properties_from_entity(
                            ref_entity, ref_schema, spec, visited, prefix=f"{field_id}[*]"
                        )
                        result.update(nested)
    
    return result

'''

# Insert helper functions before load_state_from_openapi_yaml
pattern = r'(    return dag\n\n)(\ndef load_state_from_openapi_yaml\()'
content = re.sub(pattern, r'\1' + helper_functions + r'\2', content)

# 3. Replace the entire load_state_from_openapi_yaml function
new_function = '''def load_state_from_openapi_yaml(
    doc: str | Path,
    initial_values: Optional[Dict[str, Any]] = None,
    default_confidence: float = 0.0,
) -> State:
    """
    Build an initial State DAG from an OpenAPI YAML with x-sup extensions.

    This function:
    - Uses x-sup.root_entity to determine the starting entity
    - Creates a PropertyInstance for every property in the root entity and its nested objects
    - Each PropertyInstance has an initial snapshot with default values (or provided initial values)
    - Creates ConstraintInstance for all constraints (both self-constraints and dependencies)

    Parameters
    ----------
    doc : path or YAML string
    initial_values : optional mapping of field_id -> value (e.g., "Registration.registrant.name": "Alice")
    default_confidence : initial confidence for all constraint instances (0.0..1.0)
    
    Returns
    -------
    State : A State DAG with PropertyInstance nodes and ConstraintInstance edges
    """
    spec = _load_yaml(doc)
    
    # 1) Get root entity from x-sup
    x_sup = spec.get("x-sup", {})
    root_entity_name = x_sup.get("root_entity")
    if not root_entity_name:
        raise ValueError("x-sup.root_entity not found in OpenAPI spec")
    
    # 2) Get the root entity schema
    entities = dict(_iter_entities(spec))
    if root_entity_name not in entities:
        raise ValueError(f"Root entity '{root_entity_name}' not found in components.schemas")
    
    root_schema = entities[root_entity_name]
    
    # 3) Collect all properties from root entity and nested objects
    visited: Set[str] = set()
    all_properties = _collect_properties_from_entity(
        root_entity_name, root_schema, spec, visited
    )
    
    # 4) Create Property objects for each field
    properties: Dict[str, Property] = {}
    for field_id, (prop_schema, entity_name) in all_properties.items():
        info = Info(
            name=field_id,
            description=prop_schema.get("description", "")
        )
        
        # Collect self-constraints from JSON Schema
        constraints: List[Constraint] = []
        constraints.extend(_mk_self_constraints(field_id, prop_schema))
        
        # Add x-sup constraints if present
        x_sup_constraints = _get_ext(prop_schema, "x-sup", {}).get("constraints", [])
        if x_sup_constraints:
            constraints.extend(_mk_constraints_from_extension(field_id, x_sup_constraints))
        
        properties[field_id] = Property(
            id=field_id,
            info=info,
            constraints=constraints,
            default_value=_get_default_value(prop_schema),
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
        snapshots: List[PropertySnapshot] = []
        if value is not None:
            snapshots.append(
                PropertySnapshot(
                    id=f"{field_id}@t0",
                    status=PropertyStatusEnum.UNTOUCHED,
                    value_confidences=[
                        ValueConfidence(value=value, score=1.0)
                    ],
                    updater=None,
                    meta_data={}
                )
            )
        else:
            # Create an empty snapshot even if no value
            snapshots.append(
                PropertySnapshot(
                    id=f"{field_id}@t0",
                    status=PropertyStatusEnum.UNTOUCHED,
                    value_confidences=[],
                    updater=None,
                    meta_data={}
                )
            )
        
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
    
    # 7) Add constraint edges from x-sup constraints
    for field_id, (prop_schema, entity_name) in all_properties.items():
        x_sup_constraints = _get_ext(prop_schema, "x-sup", {}).get("constraints", [])
        
        for constraint_def in x_sup_constraints or []:
            # Check if this is a dependency constraint (references another property)
            on_field = constraint_def.get("on")
            if on_field:
                # This is a dependency: current field depends on 'on_field'
                # The edge goes from on_field -> current field_id
                
                # Resolve the on_field to full path if needed
                if "." not in on_field:
                    # Relative reference within same entity
                    parent_path = ".".join(field_id.split(".")[:-1])
                    prereq_id = f"{parent_path}.{on_field}" if parent_path else f"{root_entity_name}.{on_field}"
                else:
                    prereq_id = on_field
                
                # Only add edge if the prerequisite exists
                if prereq_id in instances:
                    # Parse the constraint
                    constraints_list = _mk_constraints_from_extension(prereq_id, [constraint_def])
                    
                    if constraints_list:
                        constraint_inst = ConstraintInstance(
                            id=f"{prereq_id}=>{field_id}",
                            constraints=constraints_list,
                            confidence=default_confidence
                        )
                        state.add_edge(
                            prereq_id=prereq_id,
                            dep_id=field_id,
                            metadata=constraint_inst
                        )
    
    return state
'''

# Find and replace the old function
pattern = r'def load_state_from_openapi_yaml\([^)]*\)[^:]*:.*?return state_dag'
content = re.sub(pattern, new_function.strip(), content, flags=re.DOTALL)

# Write the updated content
with open("langstate/readers/yaml.py", "w") as f:
    f.write(content)

print("File updated successfully!")
