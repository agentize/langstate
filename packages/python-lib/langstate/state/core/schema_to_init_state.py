"""Schema -> initial State conversion.

This module exposes a single helper `schema_to_init_state` which builds a
`State` (of FieldInstance/ConstraintInstance) from a `Schema` (of
Field/Constraint), preserving the graph topology and seeding minimal
snapshots.

Rules implemented:
- Preserve nodes and edges (same ids and direction) from Schema to State.
- For each Field node: if the Field has a default_value, create a single
  FieldSnapshot with status UNTOUCHED and one ValueConfidence(score=0.0,
  value=default_value).
- For each edge: create a ConstraintInstance. If the Schema edge carries a
  Constraint (metadata), attach it to the instance and create a single
  ConstraintSnapshot with confidence 0.0. For structural edges (metadata=None),
  the instance is created with empty constraints/snapshots.
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
	"""Create a FieldInstance from a Field, adding an initial snapshot if needed.

	If `field.default_value` is not None, a single snapshot with status
	UNTOUCHED and value confidence score 0.0 will be added.
	"""
	snapshots: List[FieldSnapshot] = []
	if field.default_value is not None:
		snapshots.append(
			FieldSnapshot(
				id=f"{field.id}#init",
				status=FieldStatusEnum.UNTOUCHED,
				value_confidence_list=[
					ValueConfidence(score=0.0, value=field.default_value)
				],
			)
		)

	return FieldInstance(id=field.id, property=field, snapshots=snapshots)


def _mk_constraint_instance(edge_id: str, metadata: Optional[Constraint]) -> ConstraintInstance:
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
	"""Convert a Schema DAG into an initial State DAG.

	Parameters
	----------
	schema : Schema
		The schema DAG (Field nodes, Constraint edge metadata).

	Returns
	-------
	State
		A new State DAG where:
		- Nodes are FieldInstance mirroring the Schema's Field nodes (same ids),
		  with an initial snapshot when default_value exists.
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
	for prereq_id, dep_id, constraint in schema.iter_edges():
		edge_id = f"{prereq_id}=>{dep_id}"
		ci = _mk_constraint_instance(edge_id, constraint)
		state.add_edge(prereq_id=prereq_id, dep_id=dep_id, metadata=ci)

	# Validate acyclic and return
	state.validate_acyclic()
	return state


__all__ = ["schema_to_init_state"]

