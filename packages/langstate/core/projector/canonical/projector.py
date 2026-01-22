"""Canonical State Projector interface for LangState.

The Canonical State Projector is responsible for:
- Receiving the interpretive state from the Mutator
- Validating constraints
- Resolving value-confidence pairs to single values
- Triggering actions when validation passes
- Updating canonical state
"""

from abc import abstractmethod

from ..base.projector import BaseProjector
from .schema import (
    CanonicalProjectionContext,
    CanonicalProjectionResult,
    CanonicalProjectionStrategy,
)


class BaseProjectorCanonicalState(
    BaseProjector[CanonicalProjectionContext, CanonicalProjectionResult]
):
    """Abstract base class for Canonical State Projector implementations.

    The Canonical State Projector receives the interpretive state (with inference
    and value-confidence pairs) from the Mutator, validates constraints, and
    produces the canonical state (with resolved values). It can also trigger
    actions when validation passes.

    This can be implemented as:
    - A conventional function (rule-based, highest confidence, etc.)
    - An LLM-based resolver (for complex disambiguation)
    - A hybrid approach

    Example usage:
        class HighestConfidenceProjector(BaseProjectorCanonicalState):
            async def project(
                self,
                context: CanonicalProjectionContext
            ) -> CanonicalProjectionResult:
                # Start with current canonical state or create new one
                new_canonical_state = (
                    context.canonical_state.copy()
                    if context.canonical_state
                    else {}
                )
                resolved = {}
                pending = []
                actions = []

                # Iterate through interpretive state fields
                for field_id, field_data in context.interpretive_state.items():
                    values = field_data.get("values", [])
                    if not values:
                        pending.append(field_id)
                        continue

                    # Find value with highest confidence
                    top_value = max(values, key=lambda x: x.get("confidence", 0))

                    if top_value.get("confidence", 0) >= context.confidence_threshold:
                        # Validate the value
                        is_valid, error = await self.validate_value(
                            field_id, top_value["value"], context.schema
                        )

                        if is_valid:
                            resolved[field_id] = top_value["value"]
                            new_canonical_state[field_id] = top_value["value"]
                            # Check if action should be triggered
                            if self._should_trigger_action(context, field_id):
                                actions.append(f"action_{field_id}")
                        else:
                            pending.append(field_id)
                    else:
                        pending.append(field_id)

                return CanonicalProjectionResult(
                    updated_state=new_canonical_state,
                    resolved_fields=resolved,
                    pending_fields=pending,
                    actions_triggered=actions
                )
    """

    @abstractmethod
    async def project(
        self, context: CanonicalProjectionContext
    ) -> CanonicalProjectionResult:
        """Resolve interpretive state to canonical state and validate.

        This method analyzes the interpretive state with value-confidence pairs,
        validates constraints, and produces a canonical state with resolved values.
        Can also trigger actions when validation passes.

        Args:
            context: CanonicalProjectionContext with interpretive state and current canonical state

        Returns:
            CanonicalProjectionResult with updated canonical state and any triggered actions
        """
        pass

    @abstractmethod
    async def can_trigger_action(self, context: CanonicalProjectionContext) -> bool:
        """Check if current state allows triggering an action.

        Args:
            context: CanonicalProjectionContext with current states

        Returns:
            Boolean indicating whether an action can be triggered
        """
        pass

    def get_strategy(self) -> CanonicalProjectionStrategy:
        """Get the current canonical projection strategy.

        Override this method to return the appropriate strategy.

        Returns:
            The canonical projection strategy being used
        """
        return CanonicalProjectionStrategy.HIGHEST_CONFIDENCE
