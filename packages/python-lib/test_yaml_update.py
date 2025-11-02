"""
Test the updated yaml.py implementation with registration.yaml
"""

import sys
sys.path.insert(0, '/Users/liqingpan/Projects/langstate/langstate/packages/python-lib')

from langstate.readers import yaml
from pathlib import Path

# Test file path
test_file = Path("/Users/liqingpan/Projects/langstate/langstate/packages/python-lib/tests/data/registeration.yaml")

print("="*80)
print("CURRENT IMPLEMENTATION TEST")
print("="*80)

try:
    # Try the existing function
    state = yaml.load_state_from_openapi_yaml(test_file)
    print(f"✓ Function executed successfully")
    print(f"✓ Return type: {type(state).__name__}")
    print(f"✓ Number of nodes: {len(state.nodes)}")
    print("\nFirst 5 node IDs:")
    for i, (node_id, node) in enumerate(list(state.nodes.items())[:5]):
        print(f"  {i+1}. {node_id}")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("EXPECTED BEHAVIOR")
print("="*80)
print("""
The function should:
1. Read x-sup.root_entity = 'Registration' from the YAML
2. Parse ALL properties of Registration including:
   - Direct properties: id, registrant, event, guests, total_price, status
   - Nested properties from registrant (Person): id, name, email
   - Nested properties from event (Event): id, name, description, schedule, capacity, remaining, pricing
   - Nested array items from guests[*] (Guest extends Person): id, name, email, invitation
   - Nested properties from invitation (Invitation): subject, body, send_at
3. Create PropertyInstance for each with initial snapshot
4. Parse constraints from x-sup sections and create ConstraintInstance edges
5. Return a State object (not DirectedAcyclicGraph)
""")
