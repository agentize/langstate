#!/usr/bin/env python3
"""
Example usage of the form loader with form utilities.
"""

import json
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

def simulate_form_usage():
    """Simulate using the form loader with form utilities."""
    print("=== Form Loader Usage Example ===")
    
    # This would normally be:
    # from khandhas.loader import load_form_from_id
    # from khandhas.utils.form import get_display_name, get_status, etc.
    
    # For demonstration, we'll simulate the process
    import yaml
    
    # Load the configuration
    config_path = Path("system_prompt_generator_legacy.yaml")
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    print(f"Loaded configuration for: {config_data.get('name')}")
    
    # Simulate the form structure
    class MockPropertyStatus:
        def __init__(self, type_name="untouched", value=None):
            self.type = type(f"PropertyStatusType.{type_name.upper()}", (), {'value': type_name})()
            self.value = value
    
    class MockPropertyInfo:
        def __init__(self, name, description, display_name):
            self.name = name
            self.description = description
            self.display_names = [type('DisplayName', (), {'value': display_name})()]
    
    class MockPropertySnapshot:
        def __init__(self, field_data):
            self.id = field_data.get('name')
            self.info = MockPropertyInfo(
                name=field_data.get('name'),
                description=field_data.get('description'),
                display_name=field_data.get('display_name')
            )
            self.status = MockPropertyStatus()
            self.property = type('Property', (), {
                'prompt_template': type('PromptTemplate', (), {
                    'generate': field_data.get('instruction_prompt_template')
                })() if 'instruction_prompt_template' in field_data else None
            })()
    
    class MockForm:
        def __init__(self, config_data):
            self.id = config_data.get('name')
            self.info = MockPropertyInfo(
                name=config_data.get('name'),
                description=config_data.get('info', {}).get('description'),
                display_name=config_data.get('name')
            )
            self.properties = [
                MockPropertySnapshot(field) 
                for field in config_data.get('fields', [])
            ]
            self.metadata = {
                'field_alias': config_data.get('field_alias'),
                'tones': config_data.get('tones', []),
                'welcome_message': config_data.get('welcome_message')
            }
    
    # Create form from configuration
    form = MockForm(config_data)
    
    # Simulate form utility functions
    def get_display_name(prop):
        return prop.info.display_names[0].value if prop.info.display_names else prop.info.name
    
    def get_status(prop):
        return prop.status.type
    
    def get_description(prop):
        return prop.info.description or ""
    
    def get_property_desc_string(prop, with_value=False):
        display_name = get_display_name(prop)
        status = get_status(prop)
        description = get_description(prop)
        value = prop.status.value
        
        desc = f"{display_name}({status.value}): {description}"
        if with_value:
            desc += f" | Value: '{value}'" if value else " | Value: (empty)"
        return desc
    
    # Use the form
    print(f"\nForm Information:")
    print(f"  ID: {form.id}")
    print(f"  Name: {form.info.name}")
    print(f"  Description: {form.info.description}")
    print(f"  Field Alias: {form.metadata.get('field_alias')}")
    print(f"  Tones: {form.metadata.get('tones')}")
    print(f"  Welcome Message: {form.metadata.get('welcome_message')}")
    
    print(f"\nProperties ({len(form.properties)}):")
    for prop in form.properties:
        prop_desc = get_property_desc_string(prop, with_value=True)
        print(f"  {prop_desc}")
        
        if prop.property.prompt_template and prop.property.prompt_template.generate:
            template_preview = prop.property.prompt_template.generate[:200] + "..." if len(prop.property.prompt_template.generate) > 200 else prop.property.prompt_template.generate
            print(f"    Template Preview: {template_preview}")
    
    print(f"\nDemonstrating form utilities:")
    print(f"  - Form has {len(form.properties)} properties")
    print(f"  - Field alias is '{form.metadata.get('field_alias')}'")
    print(f"  - Supported tones: {', '.join(form.metadata.get('tones', []))}")
    
    # Demonstrate potential workflow
    print(f"\nPotential Workflow:")
    print(f"1. Load form: load_form_from_id('{form.id}')")
    print(f"2. Check properties: {len(form.properties)} properties loaded")
    print(f"3. Get ready properties: find properties with status 'untouched'")
    print(f"4. Process properties: use prompt templates for generation")
    print(f"5. Update status: mark properties as 'generated', 'edited', or 'validated'")

if __name__ == "__main__":
    simulate_form_usage()
