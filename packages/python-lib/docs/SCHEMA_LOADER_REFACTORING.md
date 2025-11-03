# Schema Loader Refactoring Summary

## Overview
Refactored the OpenAPI YAML to Schema loader to follow better design principles where visualization is handled by the DAG class rather than being a parameter of the loader function.

## Changes Made

### 1. Added Interface Methods to Models (`langstate/models/`)

#### `Property.to_dag_node_name()` (field.py)
```python
def to_dag_node_name(self) -> str:
    """Return a string representation of this Property for DAG visualization."""
    return self.id
```

#### `Constraint.to_dag_edge_name()` (constraints.py)
```python
def to_dag_edge_name(self) -> str:
    """Return a string representation of this Constraint for DAG visualization."""
    # Build a descriptive label from active conditions
    # Returns labels like "type:string", "enum:5 values", "range:[0,100]", etc.
```

### 2. Simplified Loader Function (`langstate/readers/yaml_to_schema.py`)

#### Before:
```python
def load_schema_from_openapi_yaml(
    doc: str | Path,
    root_entity: Optional[str] = None,
    visualize: bool = True  # ❌ Visualization as parameter
) -> Schema:
    # ... loading logic ...
    
    # Visualization logic mixed in
    if visualize:
        print("Schema Structure...")
        print(_build_property_tree(properties))
        # Save Mermaid file
        # etc.
    
    return schema
```

#### After:
```python
def load_schema_from_openapi_yaml(
    doc: str | Path,
    root_entity: Optional[str] = None  # ✅ No visualize parameter
) -> Schema:
    # ... loading logic only ...
    return schema  # Clean separation of concerns
```

### 3. Updated Usage Pattern

#### Before (Mixed concerns):
```python
# Visualization happened during loading
schema = load_schema_from_openapi_yaml('api.yaml', visualize=True)
# Or suppress visualization
schema = load_schema_from_openapi_yaml('api.yaml', visualize=False)
```

#### After (Separation of concerns):
```python
# Step 1: Load schema (no visualization)
schema = load_schema_from_openapi_yaml('api.yaml')

# Step 2: Visualize using DAG methods
tree = schema.to_ascii_tree(
    node_label_fn=lambda p: p.to_dag_node_name()
)

mermaid = schema.to_mermaid(
    node_label_fn=lambda p: p.to_dag_node_name(),
    edge_label_fn=lambda c: c.to_dag_edge_name() if c else None
)

json_dict = schema.to_json_dict()

# Step 3: Save to file if needed (user's responsibility)
with open('diagram.md', 'w') as f:
    f.write("```mermaid\n")
    f.write(mermaid)
    f.write("\n```\n")
```

### 4. Removed Functions
- `_build_property_tree()` - No longer needed, use DAG's `to_ascii_tree()`

### 5. Updated Tests (`tests/test_yaml_to_schema.py`)

All tests updated to:
1. Remove `visualize=False` parameter from loader calls
2. New test `test_dag_visualization_methods()` demonstrates proper usage:
   - Load schema first
   - Call visualization methods separately
   - Verify output quality

## Benefits

### 1. **Single Responsibility Principle**
- Loader: Only responsible for loading and parsing
- DAG: Responsible for visualization
- Models: Provide string representations via interface methods

### 2. **Flexibility**
Users can now:
- Load once, visualize multiple times with different options
- Choose which visualizations to generate
- Customize output format and location
- Skip visualization entirely without extra parameters

### 3. **Testability**
- Easier to test loading separately from visualization
- Can test visualization methods independently
- Clear separation makes debugging easier

### 4. **Extensibility**
- Easy to add new visualization formats (just add methods to DAG)
- Properties and Constraints can customize their labels
- No need to modify loader for visualization changes

## Example Usage

See `examples/schema_visualization_demo.py` for a complete working example.

```python
from langstate.readers.yaml_to_schema import load_schema_from_openapi_yaml

# Load schema
schema = load_schema_from_openapi_yaml('registration.yaml')

# Visualize in different ways
print(schema.to_ascii_tree(node_label_fn=lambda p: p.to_dag_node_name()))
print(schema.to_mermaid(
    node_label_fn=lambda p: p.to_dag_node_name(),
    edge_label_fn=lambda c: c.to_dag_edge_name() if c else None
))

# Export to JSON
json_data = schema.to_json_dict()

# Access properties
for node in schema.nodes.values():
    prop = node.value
    print(f"{prop.to_dag_node_name()}: {prop.info.description}")
```

## Test Results
✅ All 12 tests passing
✅ 90% coverage on yaml_to_schema.py
✅ Demo script working correctly

## Migration Guide

If you have existing code using `visualize` parameter:

```python
# Old code:
schema = load_schema_from_openapi_yaml('api.yaml', visualize=True)

# New code:
schema = load_schema_from_openapi_yaml('api.yaml')
print(schema.to_ascii_tree(node_label_fn=lambda p: p.to_dag_node_name()))
# Save Mermaid if needed:
mermaid = schema.to_mermaid(node_label_fn=lambda p: p.to_dag_node_name())
with open('diagram.md', 'w') as f:
    f.write(f"```mermaid\n{mermaid}\n```\n")
```
