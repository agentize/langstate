"""Server models for API responses and requests."""

from typing import Optional, Any, Dict, List
import json
from datetime import datetime


class BaseModel:
    """Base model class with common functionality."""

    def __init__(self, **kwargs):
        """Initialize the model."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, BaseModel):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                result[key] = [
                    item.to_dict() if isinstance(item, BaseModel) else item
                    for item in value
                ]
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result

    def to_json(self) -> str:
        """Convert model to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """Create model from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "BaseModel":
        """Create model from JSON string."""
        return cls.from_dict(json.loads(json_str))


class ResponseModel(BaseModel):
    """Standard response model."""

    def __init__(
        self,
        success: bool = True,
        message: str = "",
        data: Optional[Any] = None,
        error: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        **kwargs,
    ):
        """Initialize response model."""
        super().__init__(**kwargs)
        self.success = success
        self.message = message
        self.data = data
        self.error = error
        self.timestamp = timestamp or datetime.now()

    def model_dump(self) -> Dict[str, Any]:
        """Convert to dictionary (Pydantic compatibility)."""
        return self.to_dict()
