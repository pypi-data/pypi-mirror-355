"""
Test configuration and fixtures for {{ project_name }}
"""
import asyncio
import pytest
from fastapi.testclient import TestClient
from tortoise import Tortoise

from src.main import create_app
from src.config import TORTOISE_ORM

# Create test config with in-memory SQLite
TEST_DB_CONFIG = TORTOISE_ORM.copy()
TEST_DB_CONFIG["connections"]["default"] = "sqlite://:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture(autouse=True, scope="function")
async def initialize_tests():
    """Initialize test database before each test."""
    await Tortoise.init(config=TEST_DB_CONFIG)
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()

@pytest.fixture
async def app():
    """Create test app."""
    app = create_app(TEST_DB_CONFIG)
    return app

@pytest.fixture
def client(app):
    """Create test client."""
    with TestClient(app) as client:
        yield client
