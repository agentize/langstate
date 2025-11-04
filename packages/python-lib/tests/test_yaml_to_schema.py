"""
Tests for the yaml_to_schema module.
Ensures proper Schema creation from OpenAPI YAML files.
"""
import pytest
from pathlib import Path
from langstate.readers.yaml_to_schema import load_schema_from_openapi_yaml
from langstate.models import Field, Schema


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
        
        # Verify all nodes contain Field objects
        for node in schema.nodes.values():
            assert isinstance(node.value, Field)
            assert node.value.id == node.id  # ID should match

    def test_field_structure(self, yaml_file):
        """Should create proper Field objects with constraints."""
        schema = load_schema_from_openapi_yaml(yaml_file)
        
        # Get a sample field
        first_prop = list(schema.nodes.values())[0].value
        
        # Verify Field attributes
        assert hasattr(first_prop, 'id')
        assert hasattr(first_prop, 'info')
        assert hasattr(first_prop.info, 'name')
        assert hasattr(first_prop, 'constraints')
        assert len(first_prop.constraints) > 0

    def test_structural_edges(self, yaml_file):
        """Should create structural edges for parent-child relationships."""
        schema = load_schema_from_openapi_yaml(yaml_file)
        
        # Count structural edges only (those added without metadata)
        structural_edges = sum(
            sum(1 for e in node.depends_on.values() if e.metadata is None)
            for node in schema.nodes.values()
        )

        # registeration.yaml has 17 structural edges
        assert structural_edges == 17

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
        
        # guests is an array - should create nodes for array and its items
        property_ids = {node.value.id for node in schema.nodes.values()}
        
        assert "Registration.guests" in property_ids
        # Array items should also be present (guests.email, guests.name, etc., not guests[*].*) 
        assert any("guests.email" in prop_id or "guests.name" in prop_id or "guests.id" in prop_id for prop_id in property_ids)

    def test_validation_features(self, yaml_file):
        """Should perform validation during load."""
        # This test verifies validation happens by checking logs/behavior
        # Actual validation is tested by error cases above
        schema = load_schema_from_openapi_yaml(yaml_file)
        
        # If validation failed, we wouldn't get here
        assert schema is not None
        assert len(schema.nodes) > 0

    def test_ascii_tree_visualization(self, yaml_file):
        """Should generate ASCII tree visualization and print to console."""
        # Load schema first (no visualization during load)
        schema = load_schema_from_openapi_yaml(yaml_file)
        
        # Verify schema is loaded correctly
        assert isinstance(schema, Schema)
        assert len(schema.nodes) == 23
        
        # Test to_ascii_tree method and print to console (string returned by DAG)
        tree_output = schema.to_ascii_tree(
            node_label_fn=lambda p: p.to_dag_node_name(),
            edge_label_fn=lambda c: c.to_dag_edge_name() if c else None
        )
        assert tree_output is not None
        assert len(tree_output) > 0
        assert "Registration" in tree_output
        
        # Print the tree to console for visual verification (delimiters only)
        print("\n" + "="*80)
        print("ASCII Tree Visualization (Nodes with Types):")
        print("="*80)
        print(tree_output)
        print("="*80 + "\n")

    def test_mermaid_visualization(self, yaml_file):
        """Should generate Mermaid diagram (string) and print to console."""
        # Load schema first (no visualization during load)
        schema = load_schema_from_openapi_yaml(yaml_file)
        
        # Verify schema is loaded correctly
        assert isinstance(schema, Schema)
        assert len(schema.nodes) == 23
        
        # Test to_mermaid method (string returned by DAG)
        mermaid_output = schema.to_mermaid(
            node_label_fn=lambda p: p.to_dag_node_name(),
            edge_label_fn=lambda c: c.to_dag_edge_name() if c else None
        )
        assert mermaid_output is not None
        assert len(mermaid_output) > 0
        assert "graph TD" in mermaid_output

        # Print the Mermaid diagram to console (delimiters only)
        print("\n" + "="*80)
        print("Mermaid Diagram:")
        print("="*80)
        print(mermaid_output)
        print("="*80 + "\n")

    def test_dot_visualization(self, yaml_file):
        """Should generate Graphviz DOT (string) and print to console."""
        # Load schema first (no visualization during load)
        schema = load_schema_from_openapi_yaml(yaml_file)

        # Verify schema is loaded correctly
        assert isinstance(schema, Schema)
        assert len(schema.nodes) == 23

        # Test to_dot method (string returned by DAG)
        dot_output = schema.to_dot()
        assert isinstance(dot_output, str)
        assert len(dot_output) > 0
        assert "digraph DAG" in dot_output

        # Print DOT to console (delimiters only)
        print("\n" + "="*80)
        print("Graphviz DOT:")
        print("="*80)
        print(dot_output)
        print("="*80 + "\n")

    def test_json_dict_export(self, yaml_file):
        """Should export schema to JSON string (formatted in DAG) and validate."""
        # Load schema first (no visualization during load)
        schema = load_schema_from_openapi_yaml(yaml_file)
        
        # Verify schema is loaded correctly
        assert isinstance(schema, Schema)
        assert len(schema.nodes) == 23
        
        # Test to_json string method (formatting handled by DAG)
        json_str = schema.to_json(pretty=True, indent=2)
        assert isinstance(json_str, str)
        assert len(json_str) > 0

        # Print JSON to console for visual verification (delimiters only)
        print("\n" + "="*80)
        print("JSON Dictionary Export:")
        print("="*80)
        print(json_str)
        print("="*80 + "\n")

        # Parse back to validate structure
        import json
        json_dict = json.loads(json_str)
        assert json_dict is not None
        assert "nodes" in json_dict
        assert "edges" in json_dict
        assert json_dict["node_count"] == 23
        # Total edges should be at least structural ones; additional constraint edges may be present
        assert json_dict["edge_count"] >= 17

        # Verify node structure
        assert len(json_dict["nodes"]) == 23
        assert len(json_dict["edges"]) >= 17

        # Verify structural edge count remains constant (metadata == None)
        structural_edges = [e for e in json_dict["edges"] if e.get("metadata") is None]
        assert len(structural_edges) == 17

        # If constraints were processed, expect at least one edge with metadata
        assert any(e.get("metadata") is not None for e in json_dict["edges"])  # at least one constraint edge

        # Check that nodes have expected structure
        for node in json_dict["nodes"]:
            assert "id" in node
            assert "value" in node
