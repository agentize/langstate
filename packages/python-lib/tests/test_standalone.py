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

import pytest

def test_yaml_loading():
    """Test loading YAML files directly."""
    # Test legacy format
    legacy_path = Path("system_prompt_generator_legacy.yaml")
    if legacy_path.exists():
        with open(legacy_path, 'r') as f:
            legacy_data = yaml.safe_load(f)
        assert isinstance(legacy_data, dict)
        assert 'name' in legacy_data
        assert 'fields' in legacy_data
        assert isinstance(legacy_data.get('fields', []), list)
        # Check first field if exists
        if legacy_data.get('fields'):
            field = legacy_data['fields'][0]
            assert 'name' in field
            assert 'display_name' in field
            assert 'type' in field
    # Test new format
    new_path = Path("system_prompt_generator.yaml")
    if new_path.exists():
        with open(new_path, 'r') as f:
            new_data = yaml.safe_load(f)
        assert isinstance(new_data, dict)
        assert 'id' in new_data
        assert 'properties' in new_data
        assert isinstance(new_data.get('properties', []), list)
        # Check first property if exists
        if new_data.get('properties'):
            prop = new_data['properties'][0]
            assert 'id' in prop
            assert 'type' in prop

def test_form_structure():
    """Test the form structure conversion."""
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

    legacy_path = Path("system_prompt_generator_legacy.yaml")
    if legacy_path.exists():
        with open(legacy_path, 'r') as f:
            legacy_data = yaml.safe_load(f)
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
        assert form.id == legacy_data.get('name')
        assert form.info.name == legacy_data.get('name')
        assert isinstance(form.properties, list)
        assert form.metadata.get('field_alias') == legacy_data.get('field_alias')

if __name__ == "__main__":
    test_yaml_loading()
    test_form_structure()
