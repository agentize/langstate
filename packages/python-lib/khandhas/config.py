"""Configuration module."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
import os


class Config(BaseModel):
    """Configuration for Khandhas."""

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port", ge=1, le=65535)
    debug: bool = Field(default=False, description="Debug mode")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    log_level: str = Field(default="INFO", description="Logging level")
    cors_origins: List[str] = Field(
        default_factory=lambda: ["*"], description="CORS origins"
    )
    api_prefix: str = Field(default="/api/v1", description="API prefix")

    # Database configuration
    database_url: Optional[str] = Field(default=None, description="Database URL")

    # Security
    secret_key: str = Field(
        default="your-secret-key-here", description="Secret key for JWT"
    )
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration"
    )

    # Additional settings
    max_upload_size: int = Field(
        default=10 * 1024 * 1024, description="Max upload size in bytes"
    )

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        return cls(
            host=os.getenv("KHANDHAS_HOST", "0.0.0.0"),
            port=int(os.getenv("KHANDHAS_PORT", "8000")),
            debug=os.getenv("KHANDHAS_DEBUG", "false").lower() == "true",
            reload=os.getenv("KHANDHAS_RELOAD", "false").lower() == "true",
            log_level=os.getenv("KHANDHAS_LOG_LEVEL", "INFO"),
            cors_origins=os.getenv("KHANDHAS_CORS_ORIGINS", "*").split(","),
            api_prefix=os.getenv("KHANDHAS_API_PREFIX", "/api/v1"),
            database_url=os.getenv("KHANDHAS_DATABASE_URL"),
            secret_key=os.getenv("KHANDHAS_SECRET_KEY", "your-secret-key-here"),
            access_token_expire_minutes=int(
                os.getenv("KHANDHAS_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
            ),
            max_upload_size=int(
                os.getenv("KHANDHAS_MAX_UPLOAD_SIZE", str(10 * 1024 * 1024))
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return self.model_dump()
