"""Test the simplified yaml_simplified.py implementation"""

from pathlib import Path
from langstate.readers.yaml_simplified import load_state_from_openapi_yaml
from langstate.models import State

# Test file
test_file = Path("tests/data/registeration.yaml")

print("="*80)
print("Testing yaml_simplified.py with prance")
print("="*80)

try:
    # Load state
    state = load_state_from_openapi_yaml(test_file)
    
    print(f"✅ SUCCESS!")
    print(f"✅ Return type: {type(state).__name__}")
    print(f"✅ Is State: {isinstance(state, State)}")
    print(f"✅ Number of nodes: {len(state.nodes)}")
    
    print("\n" + "="*80)
    print("All Property IDs (sorted):")
    print("="*80)
    for i, node_id in enumerate(sorted(state.nodes.keys()), 1):
        node = state.nodes[node_id]
        snapshots = node.value.snapshots
        status = snapshots[0].status if snapshots else "N/A"
        print(f"{i:3d}. {node_id:50s} [{status}]")
    
    print("\n" + "="*80)
    print("Constraint Edges:")
    print("="*80)
    edge_count = 0
    for prereq_id, dep_id, constraint_inst in state.iter_edges():
        edge_count += 1
        print(f"{edge_count}. {prereq_id} => {dep_id}")
        print(f"   Constraints: {len(constraint_inst.constraints)}")
        print(f"   Confidence: {constraint_inst.confidence}")
    
    if edge_count == 0:
        print("(No constraint edges found)")
    
    print("\n" + "="*80)
    print("VERIFICATION:")
    print("="*80)
    
    # Check for expected nodes
    expected_nodes = [
        "Registration.id",
        "Registration.registrant",
        "Registration.event",
        "Registration.guests",
        "Registration.total_price",
        "Registration.status",
    ]
    
    for expected in expected_nodes:
        if expected in state.nodes:
            print(f"✅ Found: {expected}")
        else:
            print(f"❌ Missing: {expected}")
    
    print("\n✅ Test completed successfully!")
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
