#!/usr/bin/env python3
"""Quick test to verify constraint refactoring works correctly."""

from langstate.models import (
    Info, 
    AllowDisallowCondition,
    RangeCondition,
    ValueSimilarityCondition,
    RegexCondition,
    PromptCondition,
    StatusCondition,
    ValueTypeCondition,
    Constraint,
    Range,
    Pattern,
    Similarity,
    Prompt,
)

def test_wrapper_types():
    """Test that wrapper types work correctly."""
    
    # Test Range
    age_range = Range(min=18.0, max=65.0, inclusive_min=True, inclusive_max=True)
    assert age_range.min == 18.0
    assert age_range.max == 65.0
    print("✓ Range type works correctly")
    
    # Test Pattern
    email_pattern = Pattern(pattern=r'^[a-z]+@[a-z]+\.[a-z]+$')
    assert email_pattern.pattern == r'^[a-z]+@[a-z]+\.[a-z]+$'
    print("✓ Pattern type works correctly")
    
    # Test Similarity
    sim = Similarity(reference="test", threshold=0.8)
    assert sim.reference == "test"
    assert sim.threshold == 0.8
    print("✓ Similarity type works correctly")
    
    # Test Prompt
    p = Prompt(prompt="Check if valid")
    assert p.prompt == "Check if valid"
    print("✓ Prompt type works correctly")
    
    print("\n✅ All wrapper types work correctly!")

def test_all_constraints_are_subclasses():
    """Verify all specific conditions are subclasses of AllowDisallowCondition."""
    
    # Test RangeCondition with Range wrapper
    range_cond = RangeCondition(
        allowed=[Range(min=0.0, max=100.0)],
        info=Info(name='test_range')
    )
    assert isinstance(range_cond, AllowDisallowCondition), "RangeCondition should be AllowDisallowCondition"
    assert len(range_cond.allowed) == 1
    assert isinstance(range_cond.allowed[0], Range)
    print("✓ RangeCondition is AllowDisallowCondition[Range]")
    
    # Test ValueSimilarityCondition with Similarity wrapper
    sim_cond = ValueSimilarityCondition(
        allowed=[Similarity(reference="test", threshold=0.8)],
        info=Info(name='test_similarity')
    )
    assert isinstance(sim_cond, AllowDisallowCondition), "ValueSimilarityCondition should be AllowDisallowCondition"
    assert len(sim_cond.allowed) == 1
    assert isinstance(sim_cond.allowed[0], Similarity)
    print("✓ ValueSimilarityCondition is AllowDisallowCondition[Similarity]")
    
    # Test RegexCondition with Pattern wrapper
    regex_cond = RegexCondition(
        allowed=[Pattern(pattern=r'^\d+$')],
        info=Info(name='test_regex')
    )
    assert isinstance(regex_cond, AllowDisallowCondition), "RegexCondition should be AllowDisallowCondition"
    assert len(regex_cond.allowed) == 1
    assert isinstance(regex_cond.allowed[0], Pattern)
    print("✓ RegexCondition is AllowDisallowCondition[Pattern]")
    
    # Test PromptCondition with Prompt wrapper
    prompt_cond = PromptCondition(
        allowed=[Prompt(prompt="Is this valid?")],
        info=Info(name='test_prompt')
    )
    assert isinstance(prompt_cond, AllowDisallowCondition), "PromptCondition should be AllowDisallowCondition"
    assert len(prompt_cond.allowed) == 1
    assert isinstance(prompt_cond.allowed[0], Prompt)
    print("✓ PromptCondition is AllowDisallowCondition[Prompt]")
    
    # Test StatusCondition (already was AllowDisallowCondition)
    status_cond = StatusCondition(
        allowed=['validated'],
        info=Info(name='test_status')
    )
    assert isinstance(status_cond, AllowDisallowCondition), "StatusCondition should be AllowDisallowCondition"
    print("✓ StatusCondition is AllowDisallowCondition[FieldStatus]")
    
    # Test ValueTypeCondition (already was AllowDisallowCondition)
    from langstate.models import ValueType
    type_cond = ValueTypeCondition(
        allowed=[ValueType.STRING],
        info=Info(name='test_type')
    )
    assert isinstance(type_cond, AllowDisallowCondition), "ValueTypeCondition should be AllowDisallowCondition"
    print("✓ ValueTypeCondition is AllowDisallowCondition[ValueType]")
    
    print("\n✅ All constraint conditions are properly subclassed from AllowDisallowCondition!")

def test_constraints_in_constraint_object():
    """Test that constraints can be used in Constraint objects."""
    
    # Create a Constraint with multiple condition types using wrapper objects
    constraint = Constraint(
        conditions=[
            AllowDisallowCondition(allowed=['a', 'b', 'c'], info=Info(name='enum')),
            RangeCondition(allowed=[Range(min=0, max=100)], info=Info(name='range')),
            RegexCondition(allowed=[Pattern(pattern=r'^\w+$')], info=Info(name='pattern')),
        ]
    )
    
    assert len(constraint.conditions) == 3, "Should have 3 conditions"
    print("✓ Constraint can hold multiple condition types with wrappers")
    
    # Test edge name generation
    edge_name = constraint.to_dag_edge_name()
    assert 'enum' in edge_name and 'range' in edge_name and 'pattern' in edge_name
    print(f"✓ Constraint edge name: {edge_name}")
    
    print("\n✅ Constraints work correctly with refactored condition classes!")

def test_multiple_ranges():
    """Test that RangeCondition can have multiple Range objects."""
    
    # Multiple valid ranges
    multi_range = RangeCondition(
        allowed=[
            Range(min=0.0, max=50.0),
            Range(min=75.0, max=100.0)
        ],
        info=Info(name='multi_range')
    )
    
    assert len(multi_range.allowed) == 2
    assert multi_range.allowed[0].min == 0.0
    assert multi_range.allowed[0].max == 50.0
    assert multi_range.allowed[1].min == 75.0
    assert multi_range.allowed[1].max == 100.0
    print("✓ RangeCondition supports multiple Range objects")
    
    print("\n✅ Multiple ranges work correctly!")

if __name__ == '__main__':
    try:
        test_wrapper_types()
        test_all_constraints_are_subclasses()
        test_constraints_in_constraint_object()
        test_multiple_ranges()
        print("\n🎉 All tests passed! Constraint refactoring with wrapper types is successful.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
