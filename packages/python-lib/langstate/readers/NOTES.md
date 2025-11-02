# OpenAPI YAML Reader Notes

## aiopenapi3 Reference Handling

**Important:** aiopenapi3 uses `"ref"` (without the `$`) in its serialized dictionary output, not `"$ref"` as you might expect from the OpenAPI specification.

### Example

Original OpenAPI YAML:
```yaml
properties:
  registrant:
    $ref: '#/components/schemas/Person'
```

After `_schema_to_dict()` on aiopenapi3 Schema object:
```python
{
  "ref": "#/components/schemas/Person",  # Note: "ref" not "$ref"
  "summary": "...",
  "description": "..."
}
```

### Why This Matters

When checking for references in the code, use:
```python
if "ref" in prop_schema and prop_schema["ref"]:  # ✅ Correct
    ref_path = prop_schema["ref"]
```

**Not:**
```python
if "$ref" in prop_schema and prop_schema["$ref"]:  # ❌ Won't work with aiopenapi3
    ref_path = prop_schema["$ref"]
```

### Where This Applies

1. In `_get_properties_recursively()`:
   - Checking property $refs: `if "ref" in prop_schema`
   - Checking allOf items: `if "ref" in sub_dict`

2. **Exception:** In `_get_raw_property_xsup()`:
   - We use the raw YAML dict (not aiopenapi3 objects)
   - Raw YAML uses `"$ref"` as per OpenAPI spec
   - This is why we check `if "$ref" in prop_schema` there

### Testing

To verify reference resolution is working:
```python
from langstate.readers.yaml_simplified import load_state_from_openapi_yaml_v2

state = load_state_from_openapi_yaml_v2('registeration.yaml', {}, 1.0)

# Should have 23 nodes (Registration + all nested properties)
# If only 6 nodes, references aren't being resolved
assert len(state.nodes) == 23
```
