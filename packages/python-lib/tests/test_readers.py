"""Tests for YAML readers module."""

import pytest
from pathlib import Path
from langstate.readers.yaml import load_schema_from_openapi_yaml, load_state_from_openapi_yaml
from langstate.models import Schema, State, Property, PropertyInstance, Constraint


class TestYAMLReaders:
    """Test suite for YAML readers."""

    @pytest.fixture
    def registration_yaml_path(self):
        """Path to the registration.yaml test file."""
        return Path(__file__).parent / "data" / "registeration.yaml"

    def test_load_schema_from_registration_yaml(self, registration_yaml_path):
        """Test loading Schema from registration.yaml."""
        # Load the schema
        schema = load_schema_from_openapi_yaml(registration_yaml_path)
        
        # Verify it's a Schema (DirectedAcyclicGraph)
        assert isinstance(schema, Schema)
        
        # Print Properties
        print("\n" + "="*80)
        print("PROPERTIES (Nodes)")
        print("="*80)
        
        for property_obj in schema.nodes:
            assert isinstance(property_obj, Property)
            print(f"\nProperty ID: {property_obj.id}")
            print(f"  Description: {property_obj.info.description or 'N/A'}")
            print(f"  Constraints ({len(property_obj.constraints)}):")
            
            for i, constraint in enumerate(property_obj.constraints, 1):
                print(f"    [{i}] Target: {constraint.target_property_id}")
                if constraint.property_type:
                    print(f"        - PropertyType: allowed={constraint.property_type.allowed}, "
                          f"disallowed={constraint.property_type.disallowed}")
                if constraint.enumeration:
                    print(f"        - Enumeration: values={constraint.enumeration.values}")
                if constraint.regex:
                    print(f"        - Regex: pattern={constraint.regex.pattern}")
                if constraint.value_range:
                    vr = constraint.value_range
                    print(f"        - ValueRange: [{vr.min}, {vr.max}] "
                          f"(min_inclusive={vr.inclusive_min}, max_inclusive={vr.inclusive_max})")
                if constraint.status:
                    print(f"        - Status: allowed={constraint.status.allowed}, "
                          f"disallowed={constraint.status.disallowed}")
                if constraint.prompt:
                    print(f"        - Prompt: {constraint.prompt.prompt}")
        
        # Print Dependencies (Edges)
        print("\n" + "="*80)
        print("DEPENDENCIES (Edges)")
        print("="*80)
        
        for edge in schema.edges:
            print(f"\nEdge: {edge.source} --> {edge.target}")
            constraint = edge.payload
            assert isinstance(constraint, Constraint)
            print(f"  Constraint Target: {constraint.target_property_id}")
            
            if constraint.property_type:
                print(f"    - PropertyType: allowed={constraint.property_type.allowed}, "
                      f"disallowed={constraint.property_type.disallowed}")
            if constraint.enumeration:
                print(f"    - Enumeration: values={constraint.enumeration.values}")
            if constraint.regex:
                print(f"    - Regex: pattern={constraint.regex.pattern}")
            if constraint.value_range:
                vr = constraint.value_range
                print(f"    - ValueRange: [{vr.min}, {vr.max}] "
                      f"(min_inclusive={vr.inclusive_min}, max_inclusive={vr.inclusive_max})")
            if constraint.status:
                print(f"    - Status: allowed={constraint.status.allowed}, "
                      f"disallowed={constraint.status.disallowed}")
            if constraint.prompt:
                print(f"    - Prompt: {constraint.prompt.prompt}")
        
        # Basic assertions
        assert len(schema.nodes) > 0, "Schema should have nodes"
        print(f"\n\nTotal Properties: {len(schema.nodes)}")
        print(f"Total Dependencies: {len(schema.edges)}")
        
        # Verify some expected fields exist
        property_ids = {property_obj.id for property_obj in schema.nodes}
        assert "person.id" in property_ids or "registrant.id" in property_ids
        
    def test_load_state_from_registration_yaml(self, registration_yaml_path):
        """Test loading State from registration.yaml."""
        # Load the state with some initial values
        initial_values = {
            "registrant.name": "Alice Smith",
            "registrant.email": "alice@example.com",
            "registrant.age_group": "adult"
        }
        
        state = load_state_from_openapi_yaml(
            registration_yaml_path,
            initial_values=initial_values,
            default_confidence=0.8
        )
        
        # Verify it's a State (DirectedAcyclicGraph)
        assert isinstance(state, State)
        
        # Print Property Instances
        print("\n" + "="*80)
        print("PROPERTY INSTANCES (State Nodes)")
        print("="*80)
        
        for property_instance in state.nodes:
            assert isinstance(property_instance, PropertyInstance)
            print(f"\nPropertyInstance ID: {property_instance.id}")
            print(f"  Property: {property_instance.property.id}")
            print(f"  Snapshots ({len(property_instance.snapshots)}):")
            
            for snapshot in property_instance.snapshots:
                print(f"    - Snapshot ID: {snapshot.id}")
                print(f"      Status: {snapshot.status}")
                print(f"      Timestamp: {snapshot.timestamp}")
                print(f"      Values:")
                for vc in snapshot.value_confidences:
                    print(f"        * {vc.value} (confidence: {vc.confidence})")
        
        # Print Dependency Instances
        print("\n" + "="*80)
        print("DEPENDENCY INSTANCES (State Edges)")
        print("="*80)
        
        for edge in state.edges:
            print(f"\nDependency Edge: {edge.source} --> {edge.target}")
            dep_instance = edge.payload
            print(f"  Dependency Instance ID: {dep_instance.id}")
            print(f"  Match Confidence: {dep_instance.match_confidence}")
            print(f"  Constraints ({len(dep_instance.dependencies)}):")
            
            for i, constraint in enumerate(dep_instance.dependencies, 1):
                print(f"    [{i}] Target: {constraint.target_property_id}")
                if constraint.prompt:
                    print(f"        - Prompt: {constraint.prompt.prompt}")
                if constraint.enumeration:
                    print(f"        - Enumeration: values={constraint.enumeration.values}")
        
        # Basic assertions
        assert len(state.nodes) > 0, "State should have nodes"
        print(f"\n\nTotal Property Instances: {len(state.nodes)}")
        print(f"Total Dependency Instances: {len(state.edges)}")
        
        # Verify initial values were set
        registrant_name_instance = next(
            (fi for fi in state.nodes if fi.id == "registrant.name"),
            None
        )
        if registrant_name_instance:
            assert len(registrant_name_instance.snapshots) > 0
            assert registrant_name_instance.snapshots[0].value_confidences[0].value == "Alice Smith"
            assert registrant_name_instance.snapshots[0].value_confidences[0].confidence == 0.8
        
    def test_schema_and_state_consistency(self, registration_yaml_path):
        """Test that Schema and State have consistent structure."""
        schema = load_schema_from_openapi_yaml(registration_yaml_path)
        state = load_state_from_openapi_yaml(registration_yaml_path)
        
        # Every field in schema should have a corresponding instance in state
        schema_property_ids = {property_obj.id for property_obj in schema.nodes}
        state_property_ids = {fi.id for fi in state.nodes}
        
        assert schema_property_ids == state_property_ids, \
            "Schema and State should have the same property IDs"
        
        # Number of edges should match
        assert len(schema.edges) == len(state.edges), \
            "Schema and State should have the same number of edges"
        
        print(f"\n✓ Schema and State are consistent!")
        print(f"  - Properties: {len(schema_property_ids)}")
        print(f"  - Dependencies: {len(schema.edges)}")


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "-s"])
