"""Pydantic schemas for Action module.

This module contains all data models used by the Action interface.
"""

from enum import Enum
from typing import Annotated, Dict, Optional

from pydantic import BaseModel, Field

from core.state.state.base import BaseState



class ActionStatus(str, Enum):
    """Status of an action execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionContext(BaseModel):
    """Context provided to an action for execution."""

    canonical_state: Annotated[
        BaseState,
        Field(
            description="The canonical state with resolved field values (key: value)"
        ),
    ]
    action_type: Annotated[
        str,
        Field(default="default", description="Type of action to perform"),
    ]
    parameters: Annotated[
        Dict[str, object],
        Field(default_factory=dict, description="Additional parameters for the action"),
    ]
    metadata: Annotated[
        Dict[str, object],
        Field(default_factory=dict, description="Additional context metadata"),
    ]


class ActionResult(BaseModel):
    """Result of an action execution."""

    status: Annotated[
        ActionStatus,
        Field(description="Status of the action"),
    ]
    result_data: Annotated[
        Dict[str, object],
        Field(default_factory=dict, description="Data returned by the action"),
    ]
    error_message: Annotated[
        Optional[str],
        Field(default=None, description="Error message if action failed"),
    ]
    metadata: Annotated[
        Dict[str, object],
        Field(default_factory=dict, description="Additional metadata"),
    ]
