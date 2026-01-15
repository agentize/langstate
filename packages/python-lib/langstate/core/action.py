"""Action interface for LangState.

The Action represents the final step when validation passes in the Canonicalizer.
Actions can be triggered to perform business logic, API calls, etc.
Actions receive the canonical state (key: value) for execution.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field as PydField, ConfigDict

if TYPE_CHECKING:
    from ..models.field import State


class ActionStatus(str, Enum):
    """Status of an action execution.

    Attributes:
        PENDING: Action is waiting to be executed
        RUNNING: Action is currently executing
        SUCCESS: Action completed successfully
        FAILED: Action failed
        CANCELLED: Action was cancelled
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionContext(BaseModel):
    """Context provided to an action for execution.

    Attributes:
        canonical_state: The canonical state with resolved field values (key: value)
        action_type: Type of action to perform
        parameters: Additional parameters for the action
        metadata: Additional context metadata
    """

    canonical_state: Any  # State - canonical state with resolved values
    action_type: str = "default"
    parameters: Dict[str, Any] = PydField(default_factory=dict)
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class ActionResult(BaseModel):
    """Result of an action execution.

    Attributes:
        status: Status of the action
        result_data: Data returned by the action
        error_message: Error message if action failed
        metadata: Additional metadata
    """

    status: ActionStatus
    result_data: Dict[str, Any] = PydField(default_factory=dict)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class BaseAction(ABC):
    """Abstract base class for Action implementations.

    Actions are executed when the state is complete and ready.
    They represent the final business logic that should be performed
    with the collected data.

    Example usage:
        class RegistrationAction(BaseAction):
            async def execute(self, context: ActionContext) -> ActionResult:
                # Extract resolved values from state graph
                user_data = {}
                for node_id, node in context.state.nodes.items():
                    field_instance = node.value
                    # Get the resolved value from latest snapshot
                    if field_instance.snapshots:
                        latest = field_instance.snapshots[-1]
                        if latest.value_confidence_list:
                            top_value = max(
                                latest.value_confidence_list,
                                key=lambda x: x.score
                            )
                            user_data[node_id] = top_value.value

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
    async def validate(self, context: ActionContext) -> tuple[bool, Optional[str]]:
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
