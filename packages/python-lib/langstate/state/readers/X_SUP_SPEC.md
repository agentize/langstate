# x-sup Extension Specification for OpenAPI YAML

This document specifies the `x-sup` extension format for defining constraints and dependencies in OpenAPI YAML files. The `x-sup` extension enables you to define complex validation rules and property dependencies that go beyond standard JSON Schema constraints.

## Table of Contents

- [Overview](#overview)
- [Basic Structure](#basic-structure)
- [Root Entity Configuration](#root-entity-configuration)
- [Constraint Types](#constraint-types)
- [Constraint Locations](#constraint-locations)
- [Constraint Source Keys](#constraint-source-keys)
- [Complete Examples](#complete-examples)
- [Best Practices](#best-practices)

---

## Overview

The `x-sup` extension allows you to:

1. Specify a root entity for schema processing
2. Define property-level constraints with dependencies
3. Create top-level constraint rules
4. Express complex validation logic using multiple condition types

**Key Features:**

- **Property Dependencies**: Define constraints that depend on other properties
- **Multiple Condition Types**: Support for type, status, enumeration, regex, range, similarity, and LLM-based validation
- **Flexible Syntax**: Multiple synonyms for constraint keys to improve readability
- **Hyperedge Support**: Create multi-source constraints (multiple properties → one target)

---

## Basic Structure

### OpenAPI File with x-sup

```yaml
openapi: 3.1.0
info:
  title: My API
  version: 1.0.0

x-sup:
  root_entity: Registration  # Required: specifies the root schema
  constraints: []             # Optional: top-level constraints

components:
  schemas:
    Registration:
      type: object
      properties:
        # ... property definitions with optional x-sup constraints
```

---

## Root Entity Configuration

The `x-sup.root_entity` field specifies which schema in `components.schemas` should be used as the root for building the dependency graph.

```yaml
x-sup:
  root_entity: Registration  # Must match a schema name in components.schemas
```

**Important:**

- Required field (or can be passed as parameter to `load_schema_from_openapi_yaml`)
- Must reference an existing schema in `components.schemas`
- All property IDs will be prefixed with this entity name (e.g., `Registration.email`)

---

## Constraint Types

The `x-sup` extension supports the following constraint condition types:

### 1. Property Type Constraint (`property_type`)

Validates that a property value has one of the allowed types.

**Format (list):**

```yaml
property_type: [string, integer]
```

**Format (dict with allowed/disallowed):**

```yaml
property_type:
  allowed: [string, integer]
  disallowed: []
```

**Supported Types:**

- `string`
- `integer`
- `number`
- `boolean`
- `array`
- `object` (mapped to REFERENCE in the system)

---

### 2. Status Constraint (`status`)

Filters based on property status (e.g., validated, generated, edited).

**Format (list):**

```yaml
status: [validated, generated]
```

**Format (dict):**

```yaml
status:
  allowed: [validated, edited]
  disallowed: [stale, unknown]
```

**Note:** When `allowed` is non-empty, `disallowed` is ignored (allowlist takes precedence).

---

### 3. Enumeration Constraint (`enumeration`)

Validates that a value is in a specific set of allowed values.

**Format (list):**

```yaml
enumeration: [active, inactive, pending]
```

**Format (dict):**

```yaml
enumeration:
  allowed: [red, green, blue]
  disallowed: []
```

**Use Case:** Discrete value sets, dropdown options, status values.

---

### 4. Regex Pattern Constraint (`regex`)

Validates that a value matches a regular expression pattern.

**Format (string):**

```yaml
regex: '^[A-Z]{2}[0-9]{4}$'
```

**Format (dict):**

```yaml
regex:
  pattern: '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
```

**Use Case:** Email validation, phone numbers, postal codes, custom formats.

---

### 5. Range Constraint (`range`)

Validates that a numeric value falls within a specified range.

**Format (dict):**

```yaml
range:
  min: 0
  max: 100
  inclusive_min: true
  inclusive_max: true
```

**Fields:**

- `min` (float, required): Minimum value
- `max` (float, required): Maximum value
- `inclusive_min` (bool, optional, default: true): Include min in valid range
- `inclusive_max` (bool, optional, default: true): Include max in valid range

**Use Case:** Age validation, percentage values, quantity limits.

---

### 6. Value Similarity Constraint (`value_similarity`)

Validates that a value is similar to a reference value (using similarity metrics).

**Format (dict):**

```yaml
value_similarity:
  reference: "Expected text"
  threshold: 0.8  # 0.0 to 1.0
```

**Fields:**

- `reference` (string, required): Reference value to compare against
- `threshold` (float, required): Similarity threshold (0.0 = no requirement, 1.0 = exact match)

**Use Case:** Fuzzy matching, near-duplicate detection, semantic validation.

---

### 7. Prompt Constraint (`prompt`)

Uses an LLM prompt for validation (semantic/contextual evaluation).

**Format (string):**

```yaml
prompt: "Check if the description is appropriate for a professional setting"
```

**Format (dict):**

```yaml
prompt:
  prompt: "Validate that the comment explains the algorithm complexity"
```

**Use Case:** Semantic validation, quality assessment, complex business rules.

---

## Constraint Locations

Constraints can be defined at three levels:

### 1. Property-Level Constraints

Define constraints directly on a property schema using `x-sup.constraints`.

```yaml
components:
  schemas:
    Registration:
      type: object
      properties:
        email:
          type: string
          description: "User email address"
          x-sup:
            constraints:
              - source: registrant_type  # Depends on registrant_type property
                regex: '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
              
              - from: country  # Can also use 'from' as synonym for 'source'
                enumeration: ['.com', '.org', '.edu']
```

**Key Points:**

- Each constraint is a dictionary with a source key and condition(s)
- Multiple constraints can be defined in the list
- Constraints apply to the property they're defined on (target)

---

### 2. Array Item Constraints

For array properties, define constraints on the items schema.

```yaml
guests:
  type: array
  items:
    type: object
    properties:
      email:
        type: string
        x-sup:
          constraints:
            - source: ../guest_type  # Relative path to sibling in parent
              regex: '^.+@.+\..+$'
```

**Note:** For array items, field IDs will be like `Registration.guests.email` (no `[*]` notation in constraints).

---

### 3. Top-Level Constraints

Define constraints at the document level under `x-sup.constraints`.

```yaml
x-sup:
  root_entity: Registration
  constraints:
    - to: email              # Must specify target with 'to' or synonym
      source: registrant_type
      regex: '^.+@.+$'
    
    - target: age            # 'target' is synonym for 'to'
      from: [country, category]  # Multi-source constraint (hyperedge)
      range:
        min: 18
        max: 100
```

**Key Points:**

- Requires explicit target key (`to`, `target`, `dep`, `dep_id`, or `dst`)
- Useful for cross-cutting constraints that don't fit naturally in property definitions

---

## Constraint Source Keys

Multiple synonyms are supported for specifying source/prerequisite properties:

### Source Keys (Property-Level)

Use these in property-level constraints to specify which property(ies) the constraint depends on:

- `source` ✅ **Recommended** (avoids YAML 1.1 boolean coercion)
- `from` ✅ **Recommended**
- `on` ⚠️ (can be coerced to boolean in YAML 1.1, use with caution)
- `prereq`
- `depends_on`
- `requires`

### Target Keys (Top-Level)

Use these in top-level constraints to specify which property the constraint applies to:

- `to`
- `target`
- `dep`
- `dep_id`
- `dst`

**Example:**

```yaml
# Property-level (source keys)
x-sup:
  constraints:
    - source: country        # Recommended
      regex: '^\d{5}$'
    
    - from: [state, zip]     # Multi-source
      enumeration: [valid, verified]

# Top-level (target keys)
x-sup:
  constraints:
    - to: postal_code        # Target property
      source: country        # Source property
      regex: '^\d{5}$'
```

**YAML 1.1 Boolean Coercion Warning:**

Be careful with keys like `on`, `off`, `yes`, `no` in YAML 1.1:

```yaml
# ❌ May be interpreted as boolean true
on: registrant

# ✅ Better: use 'source' or 'from'
source: registrant
from: registrant
```

Our YAML loader is configured to preserve these as strings, but for portability, prefer `source` or `from`.

---

## Complete Examples

### Example 1: Registration Form with Email Validation

```yaml
openapi: 3.1.0
info:
  title: Registration API
  version: 1.0.0

x-sup:
  root_entity: Registration

components:
  schemas:
    Registration:
      type: object
      properties:
        registrant_type:
          type: string
          enum: [individual, corporate]
          description: "Type of registrant"
        
        email:
          type: string
          description: "Email address"
          x-sup:
            constraints:
              # Email format depends on registrant type
              - source: registrant_type
                regex: '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
        
        age:
          type: integer
          description: "Age of registrant"
          x-sup:
            constraints:
              # Age range depends on registrant type
              - source: registrant_type
                range:
                  min: 18
                  max: 120
                  inclusive_min: true
                  inclusive_max: true
```

---

### Example 2: Multi-Source Constraint (Hyperedge)

```yaml
x-sup:
  root_entity: Order

components:
  schemas:
    Order:
      type: object
      properties:
        country:
          type: string
          enum: [US, CA, UK]
        
        product_category:
          type: string
          enum: [electronics, clothing, food]
        
        shipping_method:
          type: string
          x-sup:
            constraints:
              # Shipping method depends on BOTH country AND category
              - source: [country, product_category]
                enumeration: [standard, express, overnight]
```

---

### Example 3: Nested Objects and Arrays

```yaml
x-sup:
  root_entity: Event

components:
  schemas:
    Event:
      type: object
      properties:
        event_type:
          type: string
          enum: [conference, workshop, webinar]
        
        attendees:
          type: array
          items:
            type: object
            properties:
              name:
                type: string
              
              role:
                type: string
                x-sup:
                  constraints:
                    # Role depends on event_type at parent level
                    # Note: reference uses absolute path
                    - source: Event.event_type
                      enumeration: [speaker, attendee, organizer]
```

---

### Example 4: LLM-Based Validation

```yaml
x-sup:
  root_entity: Article

components:
  schemas:
    Article:
      type: object
      properties:
        category:
          type: string
          enum: [technology, business, health]
        
        content:
          type: string
          x-sup:
            constraints:
              # Use LLM to validate content quality
              - source: category
                prompt: "Verify that the article content is relevant to the category and maintains a professional tone suitable for publication"
```

---

### Example 5: Combined Constraint Types

```yaml
x-sup:
  root_entity: UserProfile

components:
  schemas:
    UserProfile:
      type: object
      properties:
        account_status:
          type: string
          enum: [active, suspended, closed]
        
        username:
          type: string
          x-sup:
            constraints:
              # Multiple conditions: ANY can be satisfied (OR relationship)
              - source: account_status
                constraint:
                  # Must match pattern
                  regex: '^[a-zA-Z0-9_]{3,20}$'
              
              - source: account_status
                constraint:
                  # OR be in enumeration
                  enumeration: [admin, moderator, guest]
```

---

## Best Practices

### 1. Use Absolute Property IDs

When referencing properties from nested structures or arrays, use absolute IDs:

```yaml
# ✅ Good: absolute path
source: Registration.event_type

# ⚠️ Relative paths may work in some cases but can be ambiguous
source: ../event_type
```

### 2. Prefer Clear Source Keys

Use `source` or `from` to avoid YAML 1.1 boolean coercion issues:

```yaml
# ✅ Recommended
source: country
from: [state, city]

# ⚠️ Can be problematic in some YAML parsers
on: country
```

### 3. Group Related Constraints

Keep related constraints together for readability:

```yaml
email:
  type: string
  x-sup:
    constraints:
      # All email-related constraints together
      - source: user_type
        regex: '^.+@.+\..+$'
      - source: verification_status
        status: [validated]
```

### 4. Use Descriptive Constraint Names

When conditions have info/name fields (in code), use descriptive names:

```python
# In code generation
AllowDisallowCondition(
    allowed=['value1', 'value2'],
    info=Info(name='valid_values', description='Allowed values for this field')
)
```

### 5. Document Complex Constraints

Add YAML comments to explain complex constraint logic:

```yaml
shipping_cost:
  type: number
  x-sup:
    constraints:
      # Shipping cost depends on destination AND weight
      # For international (country != US): weight must be under 50lb
      - source: [country, weight]
        range:
          min: 0
          max: 500
```

### 6. Test Constraint Logic

Validate your constraints by:

1. Loading the schema: `schema = load_schema_from_openapi_yaml('api.yaml')`
2. Visualizing dependencies: `print(schema.to_ascii_tree())`
3. Checking constraint edges: `print(schema.to_mermaid())`

### 7. Avoid Circular Dependencies

The system checks for cycles, but design constraints to avoid them:

```yaml
# ❌ Bad: circular dependency
field_a:
  x-sup:
    constraints:
      - source: field_b
        # ...

field_b:
  x-sup:
    constraints:
      - source: field_a  # Circular!
        # ...
```

---

## Field ID Format

Property IDs follow this pattern:

- Root properties: `{RootEntity}.{property_name}`
- Nested properties: `{RootEntity}.{parent}.{property_name}`
- Array items: `{RootEntity}.{array_name}.{item_property}`

**Examples:**

- `Registration.email`
- `Registration.event.name`
- `Registration.guests.email` (for array items)

**Note:** The `[*]` notation is only used in visualization, not in constraint definitions.

---

## Schema Validation

The loader performs these validations:

1. **OpenAPI Version**: Must be 3.x
2. **Root Entity**: Must exist in `components.schemas`
3. **Property References**: Source/target properties must exist
4. **Constraint Validity**: Conditions must have valid structure
5. **Cycle Detection**: Constraint graph must be acyclic
6. **Type Safety**: Condition types must match property types

**Error Handling:**

- Missing properties in constraint references: Skipped silently (allows forward references)
- Invalid constraint payloads: Skipped with warning
- Malformed x-sup extensions: Raises `ValueError`

---

## Related Documentation

- **Implementation**: See `langstate/state/readers/yaml.py` for the loader implementation
- **Data Models**: See `langstate/models/constraints.py` for constraint condition classes
- **Examples**: See `tests/test_yaml_to_schema.py` for usage examples

---

## Version History

- **v1.0** (2025-11-16): Initial specification
  - Support for 7 constraint condition types
  - Multi-source constraints (hyperedges)
  - Property-level and top-level constraint definitions
  - Flexible key synonyms for readability
