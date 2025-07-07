"""Test the configuration."""

import pytest
import os
from pydantic import ValidationError
from khandhas.config import Config


def test_server_config_defaults():
    """Test configuration with default values."""
    config = Config()

    assert config.host == "0.0.0.0"
    assert config.port == 8000
    assert config.debug is False
    assert config.reload is False
    assert config.log_level == "INFO"
    assert config.cors_origins == ["*"]
    assert config.api_prefix == "/api/v1"
    assert config.secret_key == "your-secret-key-here"


def test_server_config_custom_values():
    """Test configuration with custom values."""
    config = Config(
        host="127.0.0.1",
        port=8080,
        debug=True,
        reload=True,
        log_level="DEBUG",
        cors_origins=["http://localhost:3000"],
        api_prefix="/api/v2",
        secret_key="custom-secret-key",
    )

    assert config.host == "127.0.0.1"
    assert config.port == 8080
    assert config.debug is True
    assert config.reload is True
    assert config.log_level == "DEBUG"
    assert config.cors_origins == ["http://localhost:3000"]
    assert config.api_prefix == "/api/v2"
    assert config.secret_key == "custom-secret-key"


def test_server_config_from_env():
    """Test configuration from environment variables."""
    # Set environment variables
    os.environ["KHANDHAS_HOST"] = "192.168.1.100"
    os.environ["KHANDHAS_PORT"] = "9000"
    os.environ["KHANDHAS_DEBUG"] = "true"
    os.environ["KHANDHAS_RELOAD"] = "true"
    os.environ["KHANDHAS_LOG_LEVEL"] = "DEBUG"
    os.environ["KHANDHAS_CORS_ORIGINS"] = "http://localhost:3000,http://localhost:3001"
    os.environ["KHANDHAS_API_PREFIX"] = "/api/v3"
    os.environ["KHANDHAS_SECRET_KEY"] = "env-secret-key"

    try:
        config = Config.from_env()

        assert config.host == "192.168.1.100"
        assert config.port == 9000
        assert config.debug is True
        assert config.reload is True
        assert config.log_level == "DEBUG"
        assert config.cors_origins == ["http://localhost:3000", "http://localhost:3001"]
        assert config.api_prefix == "/api/v3"
        assert config.secret_key == "env-secret-key"

    finally:
        # Clean up environment variables
        for key in [
            "KHANDHAS_HOST",
            "KHANDHAS_PORT",
            "KHANDHAS_DEBUG",
            "KHANDHAS_RELOAD",
            "KHANDHAS_LOG_LEVEL",
            "KHANDHAS_CORS_ORIGINS",
            "KHANDHAS_API_PREFIX",
            "KHANDHAS_SECRET_KEY",
        ]:
            if key in os.environ:
                del os.environ[key]


def test_server_config_to_dict():
    """Test configuration to dictionary conversion."""
    config = Config(
        host="127.0.0.1",
        port=8080,
        debug=True,
    )

    config_dict = config.to_dict()

    assert isinstance(config_dict, dict)
    assert config_dict["host"] == "127.0.0.1"
    assert config_dict["port"] == 8080
    assert config_dict["debug"] is True


def test_server_config_validation():
    """Test configuration validation."""
    # Test invalid port
    with pytest.raises(ValidationError):
        Config(port=-1)

    # Test invalid log level (should not raise error but use default)
    config = Config(log_level="INVALID")
    assert config.log_level == "INVALID"  # Should accept any string
