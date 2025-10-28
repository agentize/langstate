"""Test configuration for pytest."""

import pytest
import asyncio
from typing import Generator
import sys
import os

# Add the package to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Basic fixtures that don't require server imports
# Server-specific fixtures have been removed to avoid dependencies on optional packages


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
