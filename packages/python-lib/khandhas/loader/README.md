# Form Loader

This module provides functionality to load Form configurations from YAML or JSON files and convert them to the internal `Form` model structure.

## Features

- **Dual Format Support**: Handles both legacy format (with `fields` key) and new format (with `properties` key)
- **YAML and JSON Support**: Automatically detects and loads `.yaml` or `.json` files
- **Schema Alignment**: Converts configurations to proper `Form`, `PropertySnapshot`, and related model structures
- **Backward Compatibility**: Maintains support for existing field-based configurations

## Usage

### Basic Usage

```python
from khandhas.loader import load_form_from_id

# Load a form configuration by ID
form = load_form_from_id("system_prompt_generator")

# Access form properties
print(f"Form name: {form.info.name}")
print(f"Number of properties: {len(form.properties)}")

# Access individual properties
for prop in form.properties:
    print(f"Property: {prop.id} ({prop.status.type.value})")
    if prop.property.prompt_template:
        print(f"  Has prompt template: {prop.property.prompt_template.generate}")
```

### Using with Form Utils

```python
from khandhas.loader import load_form_from_id
from khandhas.utils.form import (
    get_display_name, get_status, get_description,
    get_all_properties_desc_string
)

# Load form
form = load_form_from_id("system_prompt_generator")

# Use utility functions
for prop in form.properties:
    display_name = get_display_name(prop)
    status = get_status(prop)
    description = get_description(prop)
    print(f"{display_name} ({status.value}): {description}")

# Get formatted description of all properties
desc_string = get_all_properties_desc_string(form.properties, with_value=True)
print(desc_string)
```

## Configuration Formats

### Legacy Format (with `fields` key)

```yaml
name: system_prompt_generator
fields:
  - name: instruction
    display_name: Instruction
    type: string
    description: A detailed system prompt template
    instruction_prompt_template: |
      Your instruction template here...
field_alias: section
tones:
  - professional
  - neutral
welcome_message: Welcome message here
info:
  name: System Prompt Generator
  description: Assistant for creating system prompts
```

### New Format (with `properties` key)

```yaml
id: system_prompt_generator
info:
  name: System Prompt Generator
  description: Assistant for creating system prompts
  display_names:
    - language: en
      value: System Prompt Generator
properties:
  - id: instruction
    info:
      name: instruction
      description: A detailed system prompt template
      display_names:
        - language: en
          value: Instruction
    prompt_template:
      generate: |
        Your instruction template here...
    type: string
    status:
      type: untouched
      value: null
metadata:
  field_alias: section
  tones:
    - professional
    - neutral
  welcome_message: Welcome message here
```

## File Structure

The loader looks for configuration files in the `/loader` directory:
- `{id}.yaml` or `{id}.json`
- Example: `system_prompt_generator.yaml`

## Error Handling

The loader will raise appropriate exceptions:
- `FileNotFoundError`: If neither YAML nor JSON file exists
- `json.JSONDecodeError`: If JSON file is invalid
- `yaml.YAMLError`: If YAML file is invalid
- `KeyError`: If required fields are missing

## Model Conversion

The loader automatically converts configurations to the proper model structure:

1. **Form**: Main container with id, info, properties, and metadata
2. **Info**: Metadata information with name, description, display names
3. **PropertySnapshot**: Individual property with status, agents, and dependencies
4. **Property**: Core property definition with type, prompt template, dependencies
5. **PropertyStatus**: Current status (untouched, generated, edited, validated)

## Examples

See the test files for complete examples:
- `test_standalone.py`: Basic YAML loading and conversion
- `system_prompt_generator_legacy.yaml`: Legacy format example
- `system_prompt_generator.yaml`: New format example
