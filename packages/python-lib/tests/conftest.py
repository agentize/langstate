"""Test configuration for pytest."""

import pytest
import asyncio
from typing import Generator
import sys
import os

# Add the package to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from khandhas import KhandhasServer, Config


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def server_config() -> Config:
    """Create a test server configuration."""
    return Config(
        host="127.0.0.1",
        port=8888,
        debug=True,
        reload=False,
        log_level="DEBUG",
        cors_origins=["*"],
        api_prefix="/api/v1",
        secret_key="test-secret-key",
    )


@pytest.fixture
def server(server_config: Config) -> KhandhasServer:
    """Create a test server instance."""
    return KhandhasServer(server_config)


@pytest.fixture
def app(server: KhandhasServer):
    """Create a test FastAPI app."""
    return server.get_app()
