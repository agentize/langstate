"""Simple test script to load and display registration.yaml data."""

from pathlib import Path
import sys

# Add parent directory to path to import langstate
sys.path.insert(0, str(Path(__file__).parent.parent))

from langstate.readers.yaml import load_schema_from_openapi_yaml, load_state_from_openapi_yaml
from langstate.models import Schema, State

def main():
    # Path to test data
    yaml_path = Path(__file__).parent / "data" / "registeration.yaml"
    
    print("="*80)
    print("LOADING SCHEMA FROM registration.yaml")
    print("="*80)
    
    # Load Schema
    schema = load_schema_from_openapi_yaml(yaml_path)
    print(f"\n✓ Schema loaded successfully!")
    print(f"  Type: {type(schema).__name__}")
    
    # Print Fields
    print("\n" + "="*80)
    # Count only nodes with actual Field values (not placeholder nodes)
    fields_with_values = [(fid, node) for fid, node in schema.nodes.items() if node.value is not None]
    print(f"FIELDS ({len(fields_with_values)} total)")
    print("="*80)
    
    for i, (field_id, field_node) in enumerate(fields_with_values, 1):
        field = field_node.value
        print(f"\n[{i}] Field ID: {field.id}")
        if field.info.description:
            print(f"    Description: {field.info.description}")
        print(f"    Constraints: {len(field.constraints)}")
        
        for j, constraint in enumerate(field.constraints, 1):
            print(f"      [{j}] Target: {constraint.target_field_id}")
            if constraint.field_type:
                print(f"          FieldType: allowed={[str(v.value) for v in constraint.field_type.allowed]}")
            if constraint.enumeration:
                print(f"          Enumeration: {constraint.enumeration.values}")
            if constraint.regex:
                print(f"          Regex: {constraint.regex.pattern}")
            if constraint.value_range:
                vr = constraint.value_range
                print(f"          ValueRange: [{vr.min}, {vr.max}]")
            if constraint.prompt:
                print(f"          Prompt: {constraint.prompt.prompt}")
    
    # Print Dependencies
    print("\n" + "="*80)
    # Count edges by iterating
    edge_count = sum(1 for _ in schema.iter_edges())
    print(f"DEPENDENCIES ({edge_count} total)")
    print("="*80)
    
    for i, (prereq_id, dep_id, constraint) in enumerate(schema.iter_edges(), 1):
        print(f"\n[{i}] {prereq_id} --> {dep_id}")
        print(f"    Constraint Target: {constraint.target_field_id}")
        
        if constraint.field_type:
            print(f"      FieldType: allowed={[str(v.value) for v in constraint.field_type.allowed]}")
        if constraint.enumeration:
            print(f"      Enumeration: {constraint.enumeration.values}")
        if constraint.prompt:
            print(f"      Prompt: {constraint.prompt.prompt}")
    
    # Load State with initial values
    print("\n\n" + "="*80)
    print("LOADING STATE FROM registration.yaml")
    print("="*80)
    
    initial_values = {
        "registrant.name": "Alice Smith",
        "registrant.email": "alice@example.com",
        "registrant.age_group": "adult"
    }
    
    state = load_state_from_openapi_yaml(yaml_path, initial_values=initial_values, default_confidence=0.8)
    print(f"\n✓ State loaded successfully!")
    print(f"  Type: {type(state).__name__}")
    
    # Print Field Instances
    print("\n" + "="*80)
    print(f"FIELD INSTANCES ({len(state.nodes)} total)")
    print("="*80)
    
    # Show only fields with values
    instances_with_values = [node.value for node in state.nodes.values() if node.value.snapshots]
    print(f"\nShowing {len(instances_with_values)} instances with initial values:")
    
    for fi in instances_with_values:
        print(f"\n  Field: {fi.id}")
        for snapshot in fi.snapshots:
            print(f"    Status: {snapshot.status}")
            for vc in snapshot.value_confidences:
                print(f"      Value: {vc.value} (confidence: {vc.confidence})")
    
    # Print Dependency Instances
    print("\n" + "="*80)
    state_edge_count = sum(1 for _ in state.iter_edges())
    print(f"DEPENDENCY INSTANCES ({state_edge_count} total)")
    print("="*80)
    
    # Show first 5 dependencies as examples
    edge_list = list(state.iter_edges())
    for i, (prereq_id, dep_id, dep_inst) in enumerate(edge_list[:5], 1):
        print(f"\n[{i}] {prereq_id} --> {dep_id}")
        print(f"    Match Confidence: {dep_inst.match_confidence}")
        print(f"    Dependencies: {len(dep_inst.dependencies)}")
        for constraint in dep_inst.dependencies:
            if constraint.prompt:
                print(f"      Prompt: {constraint.prompt.prompt}")
    
    if len(edge_list) > 5:
        print(f"\n  ... and {len(edge_list) - 5} more dependency instances")
    
    # Summary
    print("\n\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    schema_edge_count = sum(1 for _ in schema.iter_edges())
    print(f"Schema Fields: {len(schema.nodes)}")
    print(f"Schema Dependencies: {schema_edge_count}")
    print(f"State Field Instances: {len(state.nodes)}")
    print(f"State Dependency Instances: {state_edge_count}")
    print(f"Instances with Initial Values: {len(instances_with_values)}")
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    main()
