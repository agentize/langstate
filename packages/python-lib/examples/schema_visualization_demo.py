#!/usr/bin/env python3
"""
Demo: How to load and visualize OpenAPI Schema using the DAG methods.

This demonstrates the new design where:
1. load_schema_from_openapi_yaml() only loads the schema (no visualization)
2. Visualization is done by calling DAG methods on the returned Schema object
3. Property and Constraint provide to_dag_node_name() and to_dag_edge_name() methods
"""

from pathlib import Path
from langstate.readers.yaml_to_schema import load_schema_from_openapi_yaml


def main():
    # Path to the test YAML file
    yaml_file = Path(__file__).parent.parent / "tests" / "data" / "registeration.yaml"

    print("=" * 80)
    print("OpenAPI Schema Loader - Visualization Demo")
    print("=" * 80)
    print()

    # Step 1: Load the schema (no visualization during load)
    print("Step 1: Loading schema from OpenAPI YAML...")
    schema = load_schema_from_openapi_yaml(yaml_file)
    print(f"✓ Schema loaded: {len(schema.nodes)} properties, {sum(len(n.depends_on) for n in schema.nodes.values())} edges")
    print()

    # Step 2: Generate ASCII tree visualization using DAG method
    print("Step 2: Generate ASCII tree visualization...")
    print("-" * 80)
    tree_output = schema.to_ascii_tree(
        node_label_fn=lambda prop: prop.to_dag_node_name()
    )
    print(tree_output)
    print("-" * 80)
    print()

    # Step 3: Generate Mermaid diagram using DAG method
    print("Step 3: Generate Mermaid diagram...")
    mermaid_output = schema.to_mermaid(
        node_label_fn=lambda prop: prop.to_dag_node_name(),
        edge_label_fn=lambda constraint: constraint.to_dag_edge_name() if constraint else None,
        max_label_length=40
    )
    print("Mermaid diagram generated (first 500 chars):")
    print(mermaid_output[:500])
    print("...")
    print()

    # Step 4: Save Mermaid diagram to file
    print("Step 4: Save Mermaid diagram to file...")
    mermaid_path = yaml_file.parent / f"{yaml_file.stem}_schema_diagram.md"
    with open(mermaid_path, 'w') as f:
        f.write("# Schema Diagram\n\n")
        f.write(f"Generated from: `{yaml_file.name}`\n\n")
        f.write(f"Properties: {len(schema.nodes)}\n")
        f.write(f"Edges: {sum(len(n.depends_on) for n in schema.nodes.values())}\n\n")
        f.write("```mermaid\n")
        f.write(mermaid_output)
        f.write("\n```\n")
    print(f"✓ Mermaid diagram saved to: {mermaid_path}")
    print()

    # Step 5: Export to JSON
    print("Step 5: Export schema to JSON dictionary...")
    json_dict = schema.to_json_dict()
    print(f"✓ JSON export contains {json_dict['node_count']} nodes and {json_dict['edge_count']} edges")
    print()

    # Step 6: Access individual properties
    print("Step 6: Access individual property details...")
    reg_id_node = schema.nodes.get("Registration.id")
    if reg_id_node:
        prop = reg_id_node.value
        print(f"Property: {prop.to_dag_node_name()}")
        print(f"  Description: {prop.info.description}")
        print(f"  Constraints: {len(prop.constraints)}")
        if prop.constraints:
            for i, constraint in enumerate(prop.constraints, 1):
                print(f"    {i}. {constraint.to_dag_edge_name()}")
    print()

    print("=" * 80)
    print("Demo completed!")
    print("=" * 80)
    
    # Clean up
    if mermaid_path.exists():
        mermaid_path.unlink()


if __name__ == "__main__":
    main()
