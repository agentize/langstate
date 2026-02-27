"""Internal schemas for the in-memory snapshot repository."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Dict, Literal, Optional

from pydantic import BaseModel, Field


class InternalEntry(BaseModel):
    """Internal storage entry for a single snapshot version."""

    index: Annotated[int, Field(description="Zero-based position in the history list")]
    snapshot_type: Annotated[
        Literal["keyframe", "delta"],
        Field(description="Storage strategy for this entry"),
    ]
    mutator_id: Annotated[
        str, Field(description="Identifier of the mutator that produced this snapshot")
    ]
    timestamp: Annotated[datetime, Field(description="When the snapshot was recorded")]
    full_state_json: Annotated[
        Optional[str],
        Field(description="Full serialised state; set for keyframes only"),
    ] = None
    delta: Annotated[
        Optional[Dict[str, object]],
        Field(description="JSON diff from the previous entry; set for deltas only"),
    ] = None
