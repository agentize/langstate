from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
import yaml

# --- import your models ---
# Adjust import paths to your project layout
from langstate.models import Info, ValueType, Field, FieldInstance, FieldSnapshot, ValueConfidence, Constraint, FieldTypeCondition, EnumerationCondition, RegexCondition, ValueRangeCondition, FieldStatusCondition, PromptCondition, FieldDependencyInstance
from langstate.data_structure.dag import DirectedAcyclicGraph, DirectedAcyclicGraphEdge, DirectedAcyclicGraphNode

# ---------------------------
# Helpers
# ---------------------------

def _load_yaml(doc: str | Path) -> Dict[str, Any]:
    if isinstance(doc, (str, Path)) and Path(doc).exists():
        with open(doc, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    if isinstance(doc, Path):
        return yaml.safe_load(str(doc))
    return yaml.safe_load(doc)

def _value_type_from_jsonschema(t: str | List[str]) -> List[ValueType]:
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
    return out

def _mk_self_constraints(field_id: str, prop_schema: Dict[str, Any]) -> List[Constraint]:
    """Translate JSON Schema facets (type/enum/pattern/min/max) into self constraints."""
    out: List[Constraint] = []

    # type -> FieldTypeCondition
    types = prop_schema.get("type")
    vt = _value_type_from_jsonschema(types)
    if vt:
        out.append(
            Constraint(
                target_field_id=field_id,
                field_type=FieldTypeCondition(allowed=vt)
            )
        )

    # enum -> EnumerationCondition
    if "enum" in prop_schema and isinstance(prop_schema["enum"], list) and prop_schema["enum"]:
        out.append(
            Constraint(
                target_field_id=field_id,
                enumeration=EnumerationCondition(values=prop_schema["enum"])
            )
        )

    # pattern -> RegexCondition
    pattern = prop_schema.get("pattern")
    if pattern:
        out.append(
            Constraint(
                target_field_id=field_id,
                regex=RegexCondition(pattern=pattern)
            )
        )

    # numeric range -> ValueRangeCondition
    # OpenAPI/JSON Schema min/max naming
    numeric_min = prop_schema.get("minimum")
    numeric_max = prop_schema.get("maximum")
    if numeric_min is not None or numeric_max is not None:
        # Default inclusivity per JSON Schema: inclusive bounds when minimum/maximum used
        out.append(
            Constraint(
                target_field_id=field_id,
                value_range=ValueRangeCondition(
                    min=float(numeric_min if numeric_min is not None else float("-inf")),
                    max=float(numeric_max if numeric_max is not None else float("+inf")),
                    inclusive_min=True,
                    inclusive_max=True,
                )
            )
        )

    return out

def _mk_constraints_from_extension(field_id: str, items: List[Dict[str, Any]]) -> List[Constraint]:
    """Parse x-sup-constraints entries (already shaped like your Constraint)."""
    out: List[Constraint] = []
    for item in items or []:
        # Enforce/auto-fill target_field_id if omitted
        payload = dict(item)
        payload.setdefault("target_field_id", field_id)

        # Normalize nested objects into model types if present
        if "field_type" in payload and payload["field_type"]:
            ft = payload["field_type"]
            payload["field_type"] = FieldTypeCondition(
                allowed=ft.get("allowed", []),
                disallowed=ft.get("disallowed", []),
            )
        if "enumeration" in payload and payload["enumeration"]:
            payload["enumeration"] = EnumerationCondition(values=payload["enumeration"].get("values", []))
        if "regex" in payload and payload["regex"]:
            payload["regex"] = RegexCondition(pattern=payload["regex"]["pattern"])
        if "value_range" in payload and payload["value_range"]:
            vr = payload["value_range"]
            payload["value_range"] = ValueRangeCondition(
                min=float(vr["min"]),
                max=float(vr["max"]),
                inclusive_min=bool(vr.get("inclusive_min", True)),
                inclusive_max=bool(vr.get("inclusive_max", True)),
            )
        if "status" in payload and payload["status"]:
            st = payload["status"]
            payload["status"] = FieldStatusCondition(
                allowed=st.get("allowed", []),
                disallowed=st.get("disallowed", []),
            )
        if "prompt" in payload and payload["prompt"]:
            pr = payload["prompt"]
            payload["prompt"] = PromptCondition(prompt=pr["prompt"])

        c = Constraint(**payload)
        # guard: must equal source later (for edges); for self-constraints source==field_id
        if c.target_field_id != field_id:
            # leave it; these will be used for cross-field edges if desired
            pass
        out.append(c)
    return out

def _iter_entities(openapi: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    comps = openapi.get("components", {}).get("schemas", {})
    return list(comps.items())

def _entity_properties(schema: Dict[str, Any]) -> Dict[str, Any]:
    # Handle allOf inheritance by flattening $ref branches that define properties
    props: Dict[str, Any] = {}
    if "properties" in schema:
        props.update(schema["properties"])
    for branch in schema.get("allOf", []):
        if "$ref" in branch:
            # The caller must have resolved $ref beforehand if you want deep flattening.
            # Here we just skip; or you can inject a resolver later.
            continue
        if "properties" in branch:
            props.update(branch["properties"])
    return props

def _get_ext(schema: Dict[str, Any], key: str, default=None):
    return schema.get(key, default)

def _full_field_id(entity: str, prop: str) -> str:
    return f"{entity}.{prop}"

# ---------------------------
# Public API
# ---------------------------

def load_schema_from_openapi_yaml(doc: str | Path) -> DirectedAcyclicGraph[Field, Constraint]:
    """
    Build a Schema DAG from an OpenAPI 3.1 + x-sup-* YAML.

    Supported extensions:
      - x-sup-root-entity: str
      - x-sup-constraints: [Constraint...]
      - x-sup-field-dependencies (under a property): [{from, dependency, [to]}]
      - x-sup-dependencies (under a schema):        [{from, dependency, to}]  # 'to' REQUIRED here

    Rules:
      - Each dependency's payload MUST satisfy payload.target_field_id == from.
      - Field ids are materialized as "<Entity>.<property>".
    """
    spec = _load_yaml(doc)
    entities = dict(_iter_entities(spec))

    # 1) Create Field nodes
    fields: Dict[str, Field] = {}
    for entity, schema in entities.items():
        props = _entity_properties(schema)
        for prop, prop_schema in props.items():
            fid = _full_field_id(entity, prop)
            info = Info(name=fid, description=schema.get("description"))
            constraints: List[Constraint] = []

            # JSON Schema → self-constraints
            constraints.extend(_mk_self_constraints(fid, prop_schema))

            # x-sup-constraints on the property itself (optional)
            constraints.extend(_mk_constraints_from_extension(fid, _get_ext(prop_schema, "x-sup-constraints", [])))

            # Build Field
            fields[fid] = Field(
                id=fid,
                info=info,
                constraints=constraints,
                default_value=None,
                default_updaters=[],
                tags=[]
            )

    # 2) Create DAG nodes from Fields
    nodes: List[DirectedAcyclicGraphNode[Field, Constraint]] = []
    for field in fields.values():
        node = DirectedAcyclicGraphNode[Field, Constraint](id=field.id, value=field)
        nodes.append(node)

    # 3) Create DAG
    dag = DirectedAcyclicGraph[Field, Constraint](nodes=nodes)

    # 4) Add edges (source: upstream field id; target: unlocked field id)

    # 4a) Field-level dependencies
    for entity, schema in entities.items():
        props = _entity_properties(schema)
        for prop, prop_schema in props.items():
            fid_target = _full_field_id(entity, prop)
            for dep in _get_ext(prop_schema, "x-sup-field-dependencies", []) or []:
                src = dep["from"]                           # e.g., "registration.slot_ref"
                payload = dep["dependency"]                 # Constraint shape
                to_override = dep.get("to")                 # rarely needed at field level
                constraint = _mk_constraints_from_extension(src, [payload])[0]
                if constraint.target_field_id != src:
                    raise ValueError(
                        f"Dependency payload.target_field_id '{constraint.target_field_id}' "
                        f"must equal 'from' '{src}'"
                    )
                to_field = to_override or fid_target
                dag.add_edge(prereq_id=src, dep_id=to_field, metadata=constraint)

    # 4b) Schema-level dependencies (require 'to')
    for entity, schema in entities.items():
        for dep in _get_ext(schema, "x-sup-dependencies", []) or []:
            src = dep["from"]
            to_field = dep.get("to")
            if not to_field:
                raise ValueError(f"x-sup-dependencies entry under '{entity}' requires a 'to' field id.")
            payload = dep["dependency"]
            constraint = _mk_constraints_from_extension(src, [payload])[0]
            if constraint.target_field_id != src:
                raise ValueError(
                    f"Dependency payload.target_field_id '{constraint.target_field_id}' "
                    f"must equal 'from' '{src}'"
                )
            dag.add_edge(prereq_id=src, dep_id=to_field, metadata=constraint)

    return dag


def load_state_from_openapi_yaml(
    doc: str | Path,
    initial_values: Optional[Dict[str, Any]] = None,
    default_confidence: float = 0.0,
) -> DirectedAcyclicGraph[FieldInstance, FieldDependencyInstance]:
    """
    Build an initial State DAG from the same OpenAPI YAML.

    - Creates a FieldInstance for every Field (value left None unless provided in `initial_values`).
    - Creates a FieldDependencyInstance for every Schema edge, bundling that edge’s Constraint
      into `dependencies=[...]` with `match_confidence=default_confidence`.

    Parameters
    ----------
    doc : path or YAML string
    initial_values : optional mapping of field_id -> value (e.g., "registrant.name": "Alice")
    default_confidence : initial match confidence for all dependencies (0.0..1.0)
    """
    schema_dag = load_schema_from_openapi_yaml(doc)

    # 1) Node instances
    fv = initial_values or {}
    instance_nodes: List[DirectedAcyclicGraphNode[FieldInstance, FieldDependencyInstance]] = []
    instances: Dict[str, FieldInstance] = {}
    for field_node in schema_dag.nodes.values():
        field = field_node.value
        # Skip placeholder nodes that were created by add_edge but have no Field value
        if field is None:
            continue
        value = fv.get(field.id, None)
        snapshots: List[FieldSnapshot] = []
        if value is not None:
            snapshots.append(
                FieldSnapshot(
                    id=f"{field.id}@t0",
                    status="generated",             # or your own default status
                    value_confidences=[
                        ValueConfidence(value=value, confidence=default_confidence)
                    ],
                    timestamp=None,                 # let your model default/validator set if needed
                    updater=None,
                    meta_data={}
                )
            )
        field_instance = FieldInstance(id=field.id, field=field, snapshots=snapshots)
        instances[field.id] = field_instance
        instance_nodes.append(DirectedAcyclicGraphNode[FieldInstance, FieldDependencyInstance](
            id=field_instance.id,
            value=field_instance
        ))

    # 2) Create State DAG
    state_dag = DirectedAcyclicGraph[FieldInstance, FieldDependencyInstance](nodes=instance_nodes)

    # 3) Add edge instances
    for prereq_id, dep_id, constraint_metadata in schema_dag.iter_edges():
        # Skip edges where either endpoint doesn't exist (e.g., $ref not resolved)
        if prereq_id not in instances or dep_id not in instances:
            continue
        dep_inst = FieldDependencyInstance(
            id=f"{prereq_id}=>{dep_id}",
            dependencies=[constraint_metadata],    # keep list to allow OR semantics in future
            match_confidence=default_confidence
        )
        state_dag.add_edge(prereq_id=prereq_id, dep_id=dep_id, metadata=dep_inst)

    return state_dag