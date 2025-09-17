"""Data models for the server."""

from typing import Optional, Any, Dict, List, Union
import json
from datetime import datetime

try:
    from pydantic import BaseModel as PydanticBaseModel, Field
except ImportError:
    # Fallback for when Pydantic is not installed
    PydanticBaseModel = None
    Field = None


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


class RequestModel(BaseModel):
    """Base request model."""

    def __init__(self, **kwargs):
        """Initialize request model."""
        super().__init__(**kwargs)

    def validate(self) -> bool:
        """Validate the request model."""
        return True

    def get_errors(self) -> List[str]:
        """Get validation errors."""
        return []


class UserModel(BaseModel):
    """User model."""

    def __init__(
        self,
        id: Optional[str] = None,
        username: Optional[str] = None,
        email: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        **kwargs,
    ):
        """Initialize user model."""
        super().__init__(**kwargs)
        self.id = id
        self.username = username
        self.email = email
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()


class ConfigModel(BaseModel):
    """Configuration model."""

    def __init__(self, **kwargs):
        """Initialize config model."""
        super().__init__(**kwargs)

    def update(self, **kwargs):
        """Update configuration."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return getattr(self, key, default)


# Pydantic models (if available)
if PydanticBaseModel and Field:

    class PydanticResponseModel(PydanticBaseModel):
        """Pydantic response model for FastAPI."""

        success: bool = Field(default=True, description="Success status")
        message: str = Field(default="", description="Response message")
        data: Optional[Any] = Field(default=None, description="Response data")
        error: Optional[str] = Field(default=None, description="Error message")
        timestamp: datetime = Field(
            default_factory=datetime.now, description="Response timestamp"
        )

    class PydanticRequestModel(PydanticBaseModel):
        """Base Pydantic request model."""

        pass

    class PydanticUserModel(PydanticBaseModel):
        """Pydantic user model."""

        id: Optional[str] = Field(default=None, description="User ID")
        username: str = Field(..., description="Username")
        email: str = Field(..., description="Email address")
        created_at: Optional[datetime] = Field(
            default_factory=datetime.now, description="Created timestamp"
        )
        updated_at: Optional[datetime] = Field(
            default_factory=datetime.now, description="Updated timestamp"
        )

else:
    # Fallback aliases
    PydanticResponseModel = ResponseModel
    PydanticRequestModel = RequestModel
    PydanticUserModel = UserModel
