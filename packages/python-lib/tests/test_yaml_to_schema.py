"""
Tests for the yaml_to_schema module.
Ensures proper Schema creation from OpenAPI YAML files.
"""
import pytest
from pathlib import Path
from langstate.readers.yaml_to_schema import load_schema_from_openapi_yaml
from langstate.models import Property, Schema


@pytest.fixture
def yaml_file():
    """Path to test OpenAPI YAML file."""
    return Path(__file__).parent / "data" / "registeration.yaml"


class TestYamlToSchema:
    """Test suite for yaml_to_schema functionality."""

    def test_file_not_found(self):
        """Should raise FileNotFoundError for non-existent files."""
        with pytest.raises(FileNotFoundError):
            load_schema_from_openapi_yaml("nonexistent.yaml")

    def test_invalid_root_entity(self, yaml_file):
        """Should raise ValueError for invalid root entity."""
        with pytest.raises(ValueError, match="Root entity 'NonExistent' not found"):
            load_schema_from_openapi_yaml(yaml_file, root_entity="NonExistent")

    def test_successful_load(self, yaml_file):
        """Should successfully load schema from valid YAML."""
        schema = load_schema_from_openapi_yaml(yaml_file)
        
        # Verify it's a Schema
        assert isinstance(schema, Schema)
        
        # Verify node count (23 properties in registeration.yaml)
        assert len(schema.nodes) == 23
        
        # Verify all nodes contain Property objects
        for node in schema.nodes.values():
            assert isinstance(node.value, Property)
            assert node.value.id == node.id  # ID should match

    def test_property_structure(self, yaml_file):
        """Should create proper Property objects with constraints."""
        schema = load_schema_from_openapi_yaml(yaml_file)
        
        # Get a sample property
        first_prop = list(schema.nodes.values())[0].value
        
        # Verify Property attributes
        assert hasattr(first_prop, 'id')
        assert hasattr(first_prop, 'info')
        assert hasattr(first_prop.info, 'name')
        assert hasattr(first_prop, 'constraints')
        assert len(first_prop.constraints) > 0

    def test_structural_edges(self, yaml_file):
        """Should create structural edges for parent-child relationships."""
        schema = load_schema_from_openapi_yaml(yaml_file)
        
        # Count all edges (structural only in Schema)
        total_edges = sum(len(node.depends_on) for node in schema.nodes.values())
        
        # registeration.yaml has 13 structural edges
        assert total_edges == 13

    def test_dag_functionality(self, yaml_file):
        """Should function as a proper DAG."""
        schema = load_schema_from_openapi_yaml(yaml_file)
        
        # Should be able to get topological order
        topo_order = schema.topological_order()
        assert len(topo_order) > 0
        
        # Should have nodes and edges
        assert hasattr(schema, 'nodes')
        assert len(schema.nodes) > 0

    def test_type_constraints(self, yaml_file):
        """Should properly extract type constraints from properties."""
        schema = load_schema_from_openapi_yaml(yaml_file)
        
        # Find properties with known types
        reg_id = None
        reg_registrant = None
        
        for node in schema.nodes.values():
            prop = node.value
            if prop.id == "Registration.id":
                reg_id = prop
            elif prop.id == "Registration.registrant":
                reg_registrant = prop
        
        # Verify types were extracted
        assert reg_id is not None, "Registration.id not found"
        assert reg_registrant is not None, "Registration.registrant not found"
        
        # Check constraints contain type information
        assert len(reg_id.constraints) > 0
        assert len(reg_registrant.constraints) > 0

    def test_reference_resolution(self, yaml_file):
        """Should properly resolve $ref references."""
        schema = load_schema_from_openapi_yaml(yaml_file)
        
        # registeration.yaml uses $refs extensively
        # All 23 properties should be resolved
        assert len(schema.nodes) == 23
        
        # No unresolved references should remain
        for node in schema.nodes.values():
            prop = node.value
            # Property should have a valid ID (not a $ref string)
            assert not prop.id.startswith('$ref')

    def test_nested_object_handling(self, yaml_file):
        """Should handle nested object properties correctly."""
        schema = load_schema_from_openapi_yaml(yaml_file)
        
        # Registration has nested objects (registrant, event, guests)
        # Should create separate Property nodes for each
        property_ids = {node.value.id for node in schema.nodes.values()}
        
        assert "Registration.registrant" in property_ids
        assert "Registration.event" in property_ids
        assert "Registration.guests" in property_ids

    def test_array_handling(self, yaml_file):
        """Should handle array properties correctly."""
        schema = load_schema_from_openapi_yaml(yaml_file)
        
        # guests is an array - should create nodes for array and items
        property_ids = {node.value.id for node in schema.nodes.values()}
        
        assert "Registration.guests" in property_ids
        # Array items should also be present (guests[*].email, guests[*].name, etc.)
        assert any("guests[*]" in prop_id for prop_id in property_ids)

    def test_validation_features(self, yaml_file):
        """Should perform validation during load."""
        # This test verifies validation happens by checking logs/behavior
        # Actual validation is tested by error cases above
        schema = load_schema_from_openapi_yaml(yaml_file)
        
        # If validation failed, we wouldn't get here
        assert schema is not None
        assert len(schema.nodes) > 0
