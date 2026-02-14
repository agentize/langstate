"""Canonical State Projector interface for LangState.

The Canonical State Projector is responsible for:
- Receiving the current state from the Mutator
- Validating constraints
- Resolving value-confidence pairs to single values
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

    The Canonical State Projector receives current state (with inference
    and value-confidence pairs) from the Mutator, validates constraints, and
    produces a canonical projection (with resolved values).

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
                # Build a new canonical projection from current state
                new_canonical_state = {}
                resolved = {}
                pending = []

                # Iterate through state fields
                for field_id, field_data in context.state.items():
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
                        else:
                            pending.append(field_id)
                    else:
                        pending.append(field_id)

                return CanonicalProjectionResult(
                    updated_state=new_canonical_state,
                    resolved_fields=resolved,
                    pending_fields=pending
                )
    """

    @abstractmethod
    async def project(
        self, context: CanonicalProjectionContext
    ) -> CanonicalProjectionResult:
        """Resolve current state to canonical projection and validate.

        This method analyzes state with value-confidence pairs, validates
        constraints, and produces a canonical projection with resolved values.

        Args:
            context: CanonicalProjectionContext with current state and projection hints

        Returns:
            CanonicalProjectionResult with updated canonical state
        """
        pass

    def get_strategy(self) -> CanonicalProjectionStrategy:
        """Get the current canonical projection strategy.

        Override this method to return the appropriate strategy.

        Returns:
            The canonical projection strategy being used
        """
        return CanonicalProjectionStrategy.HIGHEST_CONFIDENCE
