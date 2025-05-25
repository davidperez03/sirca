import pytest
import asyncio
from httpx import AsyncClient
from app.main import app  # Import your FastAPI application

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def client():
    """
    Fixture to create an TestClient for each test function.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
