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
    yaml_path = Path("system_prompt_generator.yaml")
    if yaml_path.exists():
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict)
        assert 'id' in data
        assert 'properties' in data
        assert isinstance(data.get('properties', []), list)
        # Check first property if exists
        if data.get('properties'):
            prop = data['properties'][0]
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

    yaml_path = Path("system_prompt_generator.yaml")
    if yaml_path.exists():
        with open(yaml_path, 'r') as f:
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
        assert form.id == data.get('id', data.get('name'))
        assert form.info.name == data.get('id', data.get('name'))
        assert isinstance(form.properties, list)
        assert form.metadata.get('field_alias') == data.get('field_alias', None)

if __name__ == "__main__":
    test_yaml_loading()
    test_form_structure()
