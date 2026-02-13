"""Pydantic schemas for Evaluator module.

This module contains all data models used by the Evaluator interface.
The Evaluator runs a Mutator against a pre-state and compares
the actual post-state to an expected post-state, producing
a detailed field-by-field comparison report.
"""

from typing import Annotated, Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..mutator.base.base import BaseMutator
from ..mutator.base.schema import StructuredInput
from ..state.interpretive.base import BaseInterpretiveState
from ..state.interpretive.schema import ValueConfidence


class EvaluationContext(BaseModel):
    """Context provided to the evaluator for processing.

    Contains the mutator to execute, the pre-state to feed it,
    the expected post-state for comparison, and the input that
    drives the mutation.
    """

    mutator: Annotated[
        BaseMutator,
        Field(description="The mutator instance to evaluate."),
    ]
    pre_state: Annotated[
        BaseInterpretiveState,
        Field(description="The interpretive state before mutation."),
    ]
    expected_post_state: Annotated[
        BaseInterpretiveState,
        Field(description="The expected interpretive state after mutation."),
    ]
    mutation_input: Annotated[
        StructuredInput,
        Field(description="The structured input to feed to the mutator."),
    ]
    metadata: Annotated[
        Dict[str, Any] | None,
        Field(description="Additional metadata about the evaluation."),
    ] = None


class FieldComparison(BaseModel):
    """Comparison result for a single field between expected and actual states."""

    field_path: Annotated[
        str,
        Field(description="The field path that was compared."),
    ]
    matches: Annotated[
        bool,
        Field(description="Whether the expected and actual values match."),
    ]
    expected_value: Annotated[
        Optional[ValueConfidence],
        Field(description="The best value from the expected state, None if absent."),
    ] = None
    actual_value: Annotated[
        Optional[ValueConfidence],
        Field(description="The best value from the actual state, None if absent."),
    ] = None
    difference: Annotated[
        str | None,
        Field(
            description="Human-readable description of the mismatch, None if matching."
        ),
    ] = None


class StateComparison(BaseModel):
    """Aggregated comparison between expected and actual interpretive states."""

    fields: Annotated[
        List[FieldComparison],
        Field(description="Per-field comparison details."),
    ]
    matching_fields: Annotated[
        int,
        Field(description="Number of fields whose values match."),
    ]
    mismatched_fields: Annotated[
        int,
        Field(
            description="Number of fields present in both states but with different values."
        ),
    ]
    missing_fields: Annotated[
        int,
        Field(
            description="Number of fields present in expected state but absent from actual."
        ),
    ]
    extra_fields: Annotated[
        int,
        Field(
            description="Number of fields present in actual state but absent from expected."
        ),
    ]
    overall_match: Annotated[
        bool,
        Field(description="True when every expected field matches the actual state."),
    ]


class EvaluationResult(BaseModel):
    """Result of an evaluation run."""

    comparison: Annotated[
        StateComparison,
        Field(
            description="Detailed field-by-field comparison of expected vs actual states."
        ),
    ]
    actual_post_state: Annotated[
        BaseInterpretiveState,
        Field(description="The actual interpretive state produced by the mutator."),
    ]
    metadata: Annotated[
        Dict[str, Any] | None,
        Field(description="Additional metadata about the evaluation result."),
    ] = None
