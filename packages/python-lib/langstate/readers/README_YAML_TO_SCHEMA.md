# YAML to Schema Loader

## Overview

The `yaml_to_schema.py` module loads OpenAPI 3.1 YAML files and converts them into a `Schema` object, which is a directed acyclic graph (DAG) of `Property` definitions with structural relationships.

## Key Differences: Schema vs State

| Feature | Schema (`yaml_to_schema.py`) | State (`yaml_simplified.py`) |
|---------|------------------------------|------------------------------|
| **Node Type** | `Property` (definitions) | `PropertyInstance` (runtime instances) |
| **Node ID** | Property.id | UUID (unique per instance) |
| **Edges** | Structural only (parent→child) | Structural + x-sup constraints |
| **Purpose** | Define property structure | Runtime state representation |
| **Count** | 23 properties, 13 edges | 23 instances, 28 edges |

## Usage

```python
from langstate.readers.yaml_to_schema import load_schema_from_openapi_yaml
from pathlib import Path

# Load schema from OpenAPI YAML
# This automatically prints:
# - Summary statistics (properties count, edges count)
# - ASCII tree visualization with property types
# - Saves Mermaid diagram to {filename}_schema_diagram.md
schema = load_schema_from_openapi_yaml('path/to/openapi.yaml')

# Access properties
for node in schema.nodes.values():
    prop = node.value
    print(f"{prop.id}: {prop.info.name}")
    print(f"  Constraints: {len(prop.constraints)}")

# Get topological order
for prop_id in schema.topological_order():
    print(prop_id)
```

### Automatic Visualization

When you load a schema, you'll see:

```
================================================================================
Schema loaded from: registeration.yaml
Root entity: Registration
Properties: 23
Edges: 13
================================================================================

Schema Structure (Tree View):
├── Registration.id [string]
├── Registration.registrant [reference]
│   ├── Registration.registrant.email [string]
│   ├── Registration.registrant.id [string]
│   └── Registration.registrant.name [string]
├── Registration.event [reference]
│   ├── Registration.event.capacity [integer]
│   └── ... (more properties)
└── Registration.status [string]

Mermaid diagram saved to: registeration_schema_diagram.md
```

The Mermaid diagram can be viewed in GitHub, VS Code, or any Markdown viewer that supports Mermaid.

## Validation Features

The loader performs comprehensive validation:

1. **OpenAPI Version Check**: Ensures OpenAPI 3.1.0 compatibility
2. **Schema Structure Validation**: Verifies components.schemas exists
3. **Root Entity Validation**: Confirms root entity exists in schemas
4. **Property Resolution**: Validates all $refs and nested properties

```python
# Will raise ValueError if root entity not found
schema = load_schema_from_openapi_yaml(
    'openapi.yaml',
    root_entity='NonExistent'  # ❌ Error!
)

# Will raise FileNotFoundError
schema = load_schema_from_openapi_yaml('missing.yaml')  # ❌ Error!
```

## Structure

For the `registeration.yaml` example:

```
Schema (DAG[Property, Constraint])
├── 23 Property nodes
│   ├── Registration.id (STRING)
│   ├── Registration.status (STRING)
│   ├── Registration.registrant (REFERENCE)
│   │   ├── Registration.registrant.id
│   │   ├── Registration.registrant.name
│   │   └── Registration.registrant.email
│   ├── Registration.event (REFERENCE)
│   │   ├── Registration.event.id
│   │   ├── Registration.event.name
│   │   └── ... (7 more)
│   └── Registration.guests (ARRAY)
│       ├── Registration.guests[*].id
│       ├── Registration.guests[*].name
│       └── ... (4 more)
└── 13 structural edges (parent→child relationships)
```

## Property Types Extracted

The loader extracts type constraints from OpenAPI schemas:

- **STRING**: Text fields
- **INTEGER**: Numeric fields
- **BOOLEAN**: Boolean flags
- **ARRAY**: Collections
- **REFERENCE**: References to other objects
- **OBJECT**: Complex nested structures

## Output

Returns a `Schema` object:

```python
schema = load_schema_from_openapi_yaml('openapi.yaml')

# Schema is a DirectedAcyclicGraph
assert isinstance(schema, Schema)
assert len(schema.nodes) == 23  # For registeration.yaml

# Each node contains a Property
for node in schema.nodes.values():
    assert isinstance(node.value, Property)
    assert node.id == node.value.id  # IDs match
```

## Testing

Comprehensive test suite in `tests/test_yaml_to_schema.py`:

```bash
pytest tests/test_yaml_to_schema.py -v
```

Tests cover:
- ✅ File not found handling
- ✅ Invalid root entity handling
- ✅ Successful schema loading
- ✅ Property structure validation
- ✅ Structural edges creation
- ✅ DAG functionality
- ✅ Type constraint extraction
- ✅ Reference resolution
- ✅ Nested object handling
- ✅ Array handling
- ✅ Validation features

## Error Handling

```python
# FileNotFoundError: File doesn't exist
schema = load_schema_from_openapi_yaml('missing.yaml')

# ValueError: Invalid OpenAPI version
# ValueError: Missing components.schemas
# ValueError: Root entity not found
schema = load_schema_from_openapi_yaml('invalid.yaml')
```

## Performance

- Lazy loading: Only loads when called
- Efficient traversal: Uses aiopenapi3 for OpenAPI parsing
- Memory efficient: Creates single Property per definition (no duplicates)

## See Also

- `yaml_simplified.py` - For loading runtime State objects
- `NOTES.md` - For aiopenapi3 reference behavior documentation
- `VISUALIZATION.md` - For visualization API documentation
