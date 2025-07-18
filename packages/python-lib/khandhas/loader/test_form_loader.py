#!/usr/bin/env python3
"""
Test script for the form loader functionality.
"""

import sys
import os

# Add the package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from khandhas.loader.form_loader import load_form_from_id
from khandhas.utils.form import (
    get_display_name, get_status, get_description, 
    get_property_desc_string, get_all_properties_desc_string
)

def test_legacy_format():
    """Test loading from legacy format (with 'fields' key)."""
    print("=== Testing Legacy Format ===")
    
    try:
        form = load_form_from_id("system_prompt_generator_legacy")
        
        print(f"Form ID: {form.id}")
        print(f"Form Name: {form.info.name}")
        print(f"Form Description: {form.info.description}")
        print(f"Field Alias: {form.metadata.get('field_alias', 'field')}")
        print(f"Tones: {form.metadata.get('tones', [])}")
        print(f"Welcome Message: {form.metadata.get('welcome_message', 'N/A')}")
        
        print(f"\nProperties ({len(form.properties)}):")
        for prop in form.properties:
            print(f"  - {get_display_name(prop)} ({get_status(prop).value})")
            print(f"    Description: {get_description(prop)}")
            if prop.property.prompt_template and prop.property.prompt_template.generate:
                print(f"    Has prompt template: {len(prop.property.prompt_template.generate)} chars")
        
        # Test utility functions
        print(f"\nAll Properties Description String:")
        desc_string = get_all_properties_desc_string(form.properties, with_value=True)
        print(desc_string)
        
    except Exception as e:
        print(f"Error loading legacy format: {e}")
        import traceback
        traceback.print_exc()

def test_new_format():
    """Test loading from new format (with 'properties' key)."""
    print("\n=== Testing New Format ===")
    
    try:
        form = load_form_from_id("system_prompt_generator")
        
        print(f"Form ID: {form.id}")
        print(f"Form Name: {form.info.name}")
        print(f"Form Description: {form.info.description}")
        print(f"Field Alias: {form.metadata.get('field_alias', 'field')}")
        print(f"Tones: {form.metadata.get('tones', [])}")
        print(f"Welcome Message: {form.metadata.get('welcome_message', 'N/A')}")
        
        print(f"\nProperties ({len(form.properties)}):")
        for prop in form.properties:
            print(f"  - {get_display_name(prop)} ({get_status(prop).value})")
            print(f"    Description: {get_description(prop)}")
            if prop.property.prompt_template and prop.property.prompt_template.generate:
                print(f"    Has prompt template: {len(prop.property.prompt_template.generate)} chars")
        
        # Test utility functions
        print(f"\nAll Properties Description String:")
        desc_string = get_all_properties_desc_string(form.properties, with_value=True)
        print(desc_string)
        
    except Exception as e:
        print(f"Error loading new format: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_legacy_format()
    test_new_format()
