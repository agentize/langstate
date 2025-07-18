#!/usr/bin/env python3
"""
Standalone test script for the form loader functionality.
"""

import json
import os
import sys
import yaml
from typing import Any, Dict, List, Optional
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_yaml_loading():
    """Test loading YAML files directly."""
    print("=== Testing YAML Loading ===")
    
    # Test legacy format
    legacy_path = Path("system_prompt_generator_legacy.yaml")
    if legacy_path.exists():
        with open(legacy_path, 'r') as f:
            legacy_data = yaml.safe_load(f)
        
        print(f"Legacy format loaded successfully")
        print(f"  Name: {legacy_data.get('name')}")
        print(f"  Fields: {len(legacy_data.get('fields', []))}")
        print(f"  Field alias: {legacy_data.get('field_alias')}")
        print(f"  Tones: {legacy_data.get('tones', [])}")
        
        if legacy_data.get('fields'):
            field = legacy_data['fields'][0]
            print(f"  First field:")
            print(f"    Name: {field.get('name')}")
            print(f"    Display name: {field.get('display_name')}")
            print(f"    Type: {field.get('type')}")
            print(f"    Has instruction template: {'instruction_prompt_template' in field}")
    
    # Test new format
    new_path = Path("system_prompt_generator.yaml")
    if new_path.exists():
        with open(new_path, 'r') as f:
            new_data = yaml.safe_load(f)
        
        print(f"\nNew format loaded successfully")
        print(f"  ID: {new_data.get('id')}")
        print(f"  Properties: {len(new_data.get('properties', []))}")
        print(f"  Has metadata: {'metadata' in new_data}")
        
        if new_data.get('properties'):
            prop = new_data['properties'][0]
            print(f"  First property:")
            print(f"    ID: {prop.get('id')}")
            print(f"    Type: {prop.get('type')}")
            print(f"    Has prompt template: {'prompt_template' in prop}")

def test_form_structure():
    """Test the form structure conversion."""
    print("\n=== Testing Form Structure Conversion ===")
    
    # Mock the necessary classes for demonstration
    class MockInfo:
        def __init__(self, name=None, description=None):
            self.name = name
            self.description = description
    
    class MockForm:
        def __init__(self, id, info, properties=None, metadata=None):
            self.id = id
            self.info = info
            self.properties = properties or []
            self.metadata = metadata or {}
    
    # Test legacy format conversion
    legacy_path = Path("system_prompt_generator_legacy.yaml")
    if legacy_path.exists():
        with open(legacy_path, 'r') as f:
            legacy_data = yaml.safe_load(f)
        
        # Convert legacy format to form structure
        info = MockInfo(
            name=legacy_data.get('name'),
            description=legacy_data.get('info', {}).get('description')
        )
        
        properties = []
        for field in legacy_data.get('fields', []):
            properties.append({
                'id': field.get('name'),
                'display_name': field.get('display_name'),
                'type': field.get('type'),
                'description': field.get('description'),
                'has_template': 'instruction_prompt_template' in field
            })
        
        metadata = {
            'field_alias': legacy_data.get('field_alias'),
            'tones': legacy_data.get('tones', []),
            'welcome_message': legacy_data.get('welcome_message')
        }
        
        form = MockForm(
            id=legacy_data.get('name'),
            info=info,
            properties=properties,
            metadata=metadata
        )
        
        print(f"Converted legacy format:")
        print(f"  Form ID: {form.id}")
        print(f"  Form name: {form.info.name}")
        print(f"  Properties count: {len(form.properties)}")
        print(f"  Field alias: {form.metadata.get('field_alias')}")
        print(f"  Tones: {form.metadata.get('tones')}")
        
        for prop in form.properties:
            print(f"    Property: {prop['id']} ({prop['type']})")
            print(f"      Display: {prop['display_name']}")
            print(f"      Has template: {prop['has_template']}")

if __name__ == "__main__":
    test_yaml_loading()
    test_form_structure()
