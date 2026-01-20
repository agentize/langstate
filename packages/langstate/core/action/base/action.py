"""Action interface for LangState.

The Action represents the final step when validation passes in the Canonicalizer.
Actions can be triggered to perform business logic, API calls, etc.
Actions receive the canonical state (key: value) for execution.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from .schema import ActionContext, ActionResult


class BaseAction(ABC):
    """Abstract base class for Action implementations.

    Actions are executed when the state is complete and ready.
    They represent the final business logic that should be performed
    with the collected data.

    Example usage:
        class RegistrationAction(BaseAction):
            async def execute(self, context: ActionContext) -> ActionResult:
                # Extract resolved values from canonical state
                user_data = context.canonical_state

                try:
                    user_id = await self.user_service.register(**user_data)
                    return ActionResult(
                        status=ActionStatus.SUCCESS,
                        result_data={"user_id": user_id}
                    )
                except Exception as e:
                    return ActionResult(
                        status=ActionStatus.FAILED,
                        error_message=str(e)
                    )

    A "Final review" step can be designed as part of the business flow
    before the action is executed, allowing users to confirm all values.
    """

    @abstractmethod
    async def execute(self, context: ActionContext) -> ActionResult:
        """Execute the action with the given context.

        This method performs the actual business logic using the
        data from the canonical state.

        Args:
            context: ActionContext containing the canonical state

        Returns:
            ActionResult with the execution status and result
        """
        pass

    @abstractmethod
    async def validate(self, context: ActionContext) -> Tuple[bool, Optional[str]]:
        """Validate that the action can be executed.

        This method checks if all prerequisites are met before
        executing the action.

        Args:
            context: ActionContext to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    async def rollback(self, context: ActionContext) -> bool:
        """Rollback the action if possible.

        This method attempts to undo the action if it was partially
        executed or needs to be cancelled.

        Args:
            context: ActionContext for the action to rollback

        Returns:
            True if rollback was successful, False otherwise
        """
        pass

    def get_action_type(self) -> str:
        """Get the type identifier for this action.

        Override this method to provide a unique action type.

        Returns:
            Action type string
        """
        return "default"
