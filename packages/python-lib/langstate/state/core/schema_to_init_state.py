"""Schema -> initial Canonical State conversion.

This module exposes helpers for creating both Canonical State and Interpretive State:

- `schema_to_init_state`: Builds a Canonical State from a Schema
- `canonical_to_interpretive_state`: Builds an Interpretive State from Canonical State

The canonical state is {key: value} format - simple resolved values without
confidence information. This serves as the business state for actions.

The interpretive state is {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}
format - tracks reasoning and uncertainty. Used during conversation.

Rules implemented:
- Preserve nodes and edges (same ids and direction) from Schema to State.
- For each Field node: create FieldInstance with default_value if provided.
- For each edge: create a ConstraintInstance.
"""

from __future__ import annotations

from typing import Optional, List

from ...models.field import (
    Field,
    FieldInstance,
    FieldSnapshot,
    ValueConfidence,
    ConstraintInstance,
    ConstraintSnapshot,
    Schema,
    State,
)
from ...models.basic import FieldStatusEnum
from ...models.constraints import Constraint


def _mk_field_instance_from_field(field: Field) -> FieldInstance:
    """Create a FieldInstance from a Field for canonical state.

    For canonical state, we create a simple instance without value-confidence pairs.
    If `field.default_value` is not None, a single snapshot with status UNTOUCHED
    and the value directly (no confidence list) will be added.
    """
    snapshots: List[FieldSnapshot] = []
    if field.default_value is not None:
        # For canonical state: just store the value, no confidence
        snapshots.append(
            FieldSnapshot(
                id=f"{field.id}#init",
                status=FieldStatusEnum.UNTOUCHED,
                value_confidence_list=[],  # Empty list for canonical state
            )
        )

    return FieldInstance(id=field.id, property=field, snapshots=snapshots)


def _mk_constraint_instance(
    edge_id: str, metadata: Optional[Constraint]
) -> ConstraintInstance:
    """Create a ConstraintInstance for an edge.

    If a constraint metadata is provided, it will be included and one
    ConstraintSnapshot with confidence 0.0 will be added. For structural edges
    (metadata is None) the instance will have no constraints or snapshots.
    """
    constraints: List[Constraint] = []
    snapshots = []
    if metadata is not None:
        constraints = [metadata]
        snapshots = [
            ConstraintSnapshot(
                id=f"{edge_id}#init",
                constraint=metadata,
                confidence=0.0,
            )
        ]

    return ConstraintInstance(id=edge_id, constraints=constraints, snapshots=snapshots)


def schema_to_init_state(schema: Schema) -> State:
    """Convert a Schema DAG into an initial Canonical State DAG.

    The canonical state is {key: value} format - simple resolved values without
    confidence information. This serves as the business state for actions.

    Parameters
    ----------
    schema : Schema
            The schema DAG (Field nodes, Constraint edge metadata).

    Returns
    -------
    State
            A new Canonical State DAG where:
            - Nodes are FieldInstance mirroring the Schema's Field nodes (same ids),
              with default values stored simply (not as value-confidence pairs).
            - Edges mirror the Schema edges; each carries a ConstraintInstance,
              and if the Schema edge had a Constraint metadata, a snapshot with
              confidence 0.0 is added.
    """
    # 1) Build node map: Field.id -> FieldInstance
    state = State()

    for node_id, node in schema.nodes.items():
        field = node.value
        if field is None:
            # Defensive: create a minimal Field to keep topology if somehow missing
            # but normally Schema nodes always have a Field value.
            raise ValueError(f"Schema node '{node_id}' has no Field value")
        inst = _mk_field_instance_from_field(field)
        state.add_node(node_id, value=inst)

    # 2) Add edges with ConstraintInstance metadata, preserving direction
    # iter_hyperedges yields (source_ids: Set[str], target_id: str, metadata, edge_id)
    for source_ids, dep_id, constraint, edge_id in schema.iter_hyperedges():
        for prereq_id in source_ids:
            ci = _mk_constraint_instance(f"{prereq_id}=>{dep_id}", constraint)
            state.add_edge(prereq_id=prereq_id, dep_id=dep_id, metadata=ci)

    # Validate acyclic and return
    state.validate_acyclic()
    return state


def _mk_interpretive_field_instance(
    canonical_instance: FieldInstance,
) -> FieldInstance:
    """Create an Interpretive FieldInstance from a Canonical FieldInstance.

    For interpretive state, we convert canonical values to value-confidence pairs.
    If the canonical instance has a default value, we wrap it with confidence 0.0.

    Interpretive state format for each field:
        {inference: [{content, mutator_id}], values: [{value, confidence}]}
    """
    snapshots: List[FieldSnapshot] = []

    # Check if canonical instance has snapshots with values
    if canonical_instance.snapshots:
        for snap in canonical_instance.snapshots:
            # If there's a default value in the field property, wrap it with confidence
            if canonical_instance.property.default_value is not None:
                value_confidence_list = [
                    ValueConfidence(
                        value=canonical_instance.property.default_value,
                        confidence=0.0,  # Default values start with 0 confidence
                    )
                ]
            else:
                value_confidence_list = []

            snapshots.append(
                FieldSnapshot(
                    id=f"{canonical_instance.id}#interpretive",
                    status=FieldStatusEnum.UNTOUCHED,
                    inference_list=[],  # No inferences yet
                    value_confidence_list=value_confidence_list,
                )
            )
    elif canonical_instance.property.default_value is not None:
        # No snapshots but has default value - create initial snapshot
        snapshots.append(
            FieldSnapshot(
                id=f"{canonical_instance.id}#interpretive",
                status=FieldStatusEnum.UNTOUCHED,
                inference_list=[],
                value_confidence_list=[
                    ValueConfidence(
                        value=canonical_instance.property.default_value,
                        confidence=0.0,
                    )
                ],
            )
        )
    else:
        # No default value - create empty snapshot ready for mutations
        snapshots.append(
            FieldSnapshot(
                id=f"{canonical_instance.id}#interpretive",
                status=FieldStatusEnum.UNTOUCHED,
                inference_list=[],
                value_confidence_list=[],
            )
        )

    return FieldInstance(
        id=canonical_instance.id,
        property=canonical_instance.property,
        snapshots=snapshots,
    )


def canonical_to_interpretive_state(canonical_state: State) -> State:
    """Convert a Canonical State DAG into an Interpretive State DAG.

    The interpretive state format is:
        {key: {inference: [{content, mutator_id}], values: [{value, confidence}]}}

    This function transforms the canonical state (simple key:value) into
    interpretive state with inference tracking and value-confidence pairs.

    This is called once at initialization to prepare the state for
    receiving user input through the Mutator.

    Parameters
    ----------
    canonical_state : State
        The canonical state DAG with simple key:value format.

    Returns
    -------
    State
        A new Interpretive State DAG where:
        - Nodes are FieldInstance with inference_list and value_confidence_list
        - Default values are wrapped with confidence 0.0
        - Inference lists are empty (ready to be populated by Mutator)
        - Edges are preserved from canonical state
    """
    interpretive_state = State()

    # 1) Convert nodes: wrap canonical values with confidence
    for node_id, node in canonical_state.nodes.items():
        canonical_instance = node.value
        if canonical_instance is None:
            raise ValueError(
                f"Canonical state node '{node_id}' has no FieldInstance value"
            )

        interpretive_instance = _mk_interpretive_field_instance(canonical_instance)
        interpretive_state.add_node(node_id, value=interpretive_instance)

    # 2) Preserve edges from canonical state
    # iter_hyperedges yields (source_ids: Set[str], target_id: str, metadata, edge_id)
    for (
        source_ids,
        dep_id,
        constraint_instance,
        edge_id,
    ) in canonical_state.iter_hyperedges():
        for prereq_id in source_ids:
            interpretive_state.add_edge(
                prereq_id=prereq_id,
                dep_id=dep_id,
                metadata=constraint_instance,
            )

    # Validate acyclic and return
    interpretive_state.validate_acyclic()
    return interpretive_state


__all__ = ["schema_to_init_state", "canonical_to_interpretive_state"]
