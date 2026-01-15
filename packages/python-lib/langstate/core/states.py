"""State representations for LangState.

This module defines the core state types:
- InterpretiveState: {key: [(value, confidence)]} - stores multiple candidate values
- CanonicalState: {key: value} - stores the final business state
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field as PydField, ConfigDict


class ValueWithConfidence(BaseModel):
    """A value paired with its confidence score.

    Used in InterpretiveState to store multiple candidate values
    for a single field, each with an associated confidence score.

    Attributes:
        value: The actual value (can be any type)
        confidence: Confidence score in range [-1.0, 1.0]
            - 1.0: High confidence (confirmed by user)
            - 0.0: Neutral/unknown confidence
            - -1.0: Low confidence (likely incorrect)
    """

    value: Any
    confidence: float = PydField(default=0.0, ge=-1.0, le=1.0)

    model_config = ConfigDict(extra="allow")


class InterpretiveState(BaseModel):
    """Interpretive State representation.

    The interpretive state stores multiple candidate values for each field,
    along with confidence scores. This allows the system to track uncertainty
    and present multiple options to the user.

    Structure: {key: [(value, confidence), ...]}

    Example:
        {
            "name": [(ValueWithConfidence(value="John", confidence=0.9))],
            "age": [
                ValueWithConfidence(value=25, confidence=0.7),
                ValueWithConfidence(value=26, confidence=0.3)
            ]
        }

    Attributes:
        fields: Dictionary mapping field keys to lists of ValueWithConfidence
        metadata: Optional metadata about the state
    """

    fields: Dict[str, List[ValueWithConfidence]] = PydField(default_factory=dict)
    metadata: Dict[str, Any] = PydField(default_factory=dict)

    model_config = ConfigDict(extra="allow")

    def get_top_value(self, key: str) -> Optional[Any]:
        """Get the value with highest confidence for a given key.

        Args:
            key: The field key to look up

        Returns:
            The value with highest confidence, or None if key not found
        """
        if key not in self.fields or not self.fields[key]:
            return None

        sorted_values = sorted(
            self.fields[key], key=lambda x: x.confidence, reverse=True
        )
        return sorted_values[0].value if sorted_values else None

    def set_value(
        self, key: str, value: Any, confidence: float = 0.0, replace: bool = False
    ) -> None:
        """Set a value with confidence for a given key.

        Args:
            key: The field key
            value: The value to set
            confidence: Confidence score [-1.0, 1.0]
            replace: If True, replaces all existing values; otherwise appends
        """
        value_conf = ValueWithConfidence(value=value, confidence=confidence)

        if replace or key not in self.fields:
            self.fields[key] = [value_conf]
        else:
            self.fields[key].append(value_conf)

    def get_all_values(self, key: str) -> List[ValueWithConfidence]:
        """Get all values with confidences for a given key.

        Args:
            key: The field key to look up

        Returns:
            List of ValueWithConfidence objects, empty list if key not found
        """
        return self.fields.get(key, [])


class CanonicalState(BaseModel):
    """Canonical State (Business State) representation.

    The canonical state stores the final, resolved values for each field.
    This is the "business state" that represents the actual data extracted
    from the conversation.

    Structure: {key: value}

    Example:
        {
            "name": "John",
            "age": 25,
            "email": "john@example.com"
        }

    Attributes:
        fields: Dictionary mapping field keys to their resolved values
        metadata: Optional metadata about the state
        is_complete: Whether all required fields have been filled
    """

    fields: Dict[str, Any] = PydField(default_factory=dict)
    metadata: Dict[str, Any] = PydField(default_factory=dict)
    is_complete: bool = False

    model_config = ConfigDict(extra="allow")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a field value.

        Args:
            key: The field key
            default: Default value if key not found

        Returns:
            The field value or default
        """
        return self.fields.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a field value.

        Args:
            key: The field key
            value: The value to set
        """
        self.fields[key] = value

    def has(self, key: str) -> bool:
        """Check if a field has a value.

        Args:
            key: The field key

        Returns:
            True if the field has a value (not None)
        """
        return key in self.fields and self.fields[key] is not None

    def get_filled_fields(self) -> Dict[str, Any]:
        """Get all fields that have non-None values.

        Returns:
            Dictionary of filled fields
        """
        return {k: v for k, v in self.fields.items() if v is not None}

    def get_empty_fields(self) -> List[str]:
        """Get list of field keys that are empty (None).

        Returns:
            List of empty field keys
        """
        return [k for k, v in self.fields.items() if v is None]
