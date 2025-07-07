"""Test the server implementation."""

import pytest
from unittest.mock import Mock, patch
from khandhas import KhandhasServer, Config


def test_server_initialization():
    """Test server initialization."""
    server = KhandhasServer()

    assert server.config is not None
    assert isinstance(server.config, Config)
    assert server.app is None


def test_server_initialization_with_config():
    """Test server initialization with custom config."""
    config = Config(host="127.0.0.1", port=8080, debug=True)
    server = KhandhasServer(config)

    assert server.config == config
    assert server.config.host == "127.0.0.1"
    assert server.config.port == 8080
    assert server.config.debug is True


def test_server_create_app():
    """Test server app creation."""
    server = KhandhasServer()

    try:
        app = server.create_app()
        assert app is not None
        assert server.app is not None
        assert server.app == app
    except RuntimeError as e:
        # FastAPI not installed
        assert "FastAPI is not installed" in str(e)


def test_server_get_app():
    """Test server get_app method."""
    server = KhandhasServer()

    try:
        app = server.get_app()
        assert app is not None
        assert server.app is not None
        assert server.app == app
    except RuntimeError as e:
        # FastAPI not installed
        assert "FastAPI is not installed" in str(e)


def test_server_startup_shutdown_handlers():
    """Test adding startup and shutdown handlers."""
    server = KhandhasServer()

    startup_mock = Mock()
    shutdown_mock = Mock()

    server.add_startup_handler(startup_mock)
    server.add_shutdown_handler(shutdown_mock)

    assert startup_mock in server._startup_handlers
    assert shutdown_mock in server._shutdown_handlers


@patch("khandhas.server.uvicorn")
def test_server_run(mock_uvicorn):
    """Test server run method."""
    server = KhandhasServer()

    try:
        server.run()
        # If uvicorn is mocked, run should be called
        mock_uvicorn.run.assert_called_once()
    except RuntimeError as e:
        # uvicorn not installed
        assert "uvicorn is not installed" in str(e)


def test_server_with_debug_config():
    """Test server with debug configuration."""
    config = Config(debug=True, log_level="DEBUG")
    server = KhandhasServer(config)

    assert server.config.debug is True
    assert server.config.log_level == "DEBUG"


def test_server_with_production_config():
    """Test server with production configuration."""
    config = Config(debug=False, log_level="INFO", reload=False)
    server = KhandhasServer(config)

    assert server.config.debug is False
    assert server.config.log_level == "INFO"
    assert server.config.reload is False
