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
    
    # Test YAML loading (only new format)
    new_path = Path("system_prompt_generator.yaml")
    if new_path.exists():
        with open(new_path, 'r') as f:
            data = yaml.safe_load(f)
        print(f"YAML loaded successfully (from {new_path})")
        print(f"  ID: {data.get('id', data.get('name'))}")
        print(f"  Properties: {len(data.get('properties', []))}")
        print(f"  Has metadata: {'metadata' in data}")
        if data.get('properties'):
            prop = data['properties'][0]
            print(f"  First property:")
            print(f"    ID: {prop.get('id')}")
            print(f"    Type: {prop.get('type')}")
            print(f"    Has prompt template: {'prompt_template' in prop}")
    
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
    
    # Test form structure conversion (only new format)
    new_path = Path("system_prompt_generator.yaml")
    if new_path.exists():
        with open(new_path, 'r') as f:
            data = yaml.safe_load(f)
        info = MockInfo(
            name=data.get('id', data.get('name')),
            description=data.get('info', {}).get('description') if 'info' in data else None
        )
        properties = []
        for prop in data.get('properties', []):
            properties.append({
                'id': prop.get('id'),
                'display_name': prop.get('display_name', None),
                'type': prop.get('type'),
                'description': prop.get('description', None),
                'has_template': 'prompt_template' in prop
            })
        metadata = {
            'field_alias': data.get('field_alias', None),
            'tones': data.get('tones', []),
            'welcome_message': data.get('welcome_message', None)
        }
        form = MockForm(
            id=data.get('id', data.get('name')),
            info=info,
            properties=properties,
            metadata=metadata
        )
        print(f"Converted form structure (from {new_path}):")
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
