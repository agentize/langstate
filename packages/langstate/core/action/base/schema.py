"""Pydantic schemas for Action module.

This module contains all data models used by the Action interface.
"""

from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field

from ...state.canonical.schema import CanonicalState


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

    canonical_state: CanonicalState
    action_type: str = "default"
    parameters: Dict[str, object] = Field(default_factory=dict)
    metadata: Dict[str, object] = Field(default_factory=dict)


class ActionResult(BaseModel):
    """Result of an action execution.

    Attributes:
        status: Status of the action
        result_data: Data returned by the action
        error_message: Error message if action failed
        metadata: Additional metadata
    """

    status: ActionStatus
    result_data: Dict[str, object] = Field(default_factory=dict)
    error_message: Optional[str] = None
    metadata: Dict[str, object] = Field(default_factory=dict)
