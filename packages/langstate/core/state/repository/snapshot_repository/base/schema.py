"""Schemas for the Snapshot Repository base module."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, Field


class HistoryFilter(BaseModel):
    """Filter criteria for listing snapshot history.

    All fields are optional; when provided they narrow the result set.
    """

    from_version: Annotated[
        Optional[int], Field(description="Minimum version index (inclusive)")
    ] = None
    to_version: Annotated[
        Optional[int], Field(description="Maximum version index (inclusive)")
    ] = None
    from_time: Annotated[
        Optional[datetime], Field(description="Earliest timestamp (inclusive)")
    ] = None
    to_time: Annotated[
        Optional[datetime], Field(description="Latest timestamp (inclusive)")
    ] = None
