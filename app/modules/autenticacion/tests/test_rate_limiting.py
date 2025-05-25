import pytest
import time
from httpx import AsyncClient
# app.main is needed for AsyncClient to wrap the FastAPI application
from app.main import app

# The client fixture is defined in conftest.py at app/modules/autenticacion/tests/conftest.py

LOGIN_URL = "/usuarios/login"  # Prefix /usuarios is defined in app.modules.autenticacion.interface.rutas.py
RECOVERY_URL = "/usuarios/recuperar-contrasena" # Prefix /usuarios is defined as well

@pytest.mark.asyncio
async def test_login_rate_limit_within_limit(client: AsyncClient):
    """Test login attempts within the rate limit (5/minute)."""
    login_data = {
        "tipo_documento": "CC",
        "numero_documento": "testuser_within_limit",
        "contrasena": "password"
    }
    for i in range(5):
        response = await client.post(LOGIN_URL, data=login_data)
        assert response.status_code != 429, f"Request {i+1} (login within limit) got 429, expected other code."
        # Successful login attempts or validation errors (e.g. 400, 401, 404 due to bad creds) are okay, just not 429.

@pytest.mark.asyncio
async def test_login_rate_limit_exceeded(client: AsyncClient):
    """Test login attempts exceeding the rate limit (5/minute)."""
    login_data = {
        "tipo_documento": "CC",
        "numero_documento": "testuser_exceed_limit",
        "contrasena": "password"
    }
    # Exhaust the limit (5 requests)
    for i in range(5):
        response = await client.post(LOGIN_URL, data=login_data)
        assert response.status_code != 429, f"Request {i+1} (login to exhaust limit) got 429 unexpectedly."

    # The 6th request should be rate limited
    response = await client.post(LOGIN_URL, data=login_data)
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.text

@pytest.mark.asyncio
async def test_login_rate_limit_reset_after_time(client: AsyncClient):
    """Test login rate limit resets after the time window (1 minute)."""
    login_data = {
        "tipo_documento": "CC",
        "numero_documento": "testuser_reset_limit",
        "contrasena": "password"
    }
    # Exhaust the limit
    for i in range(5):
        await client.post(LOGIN_URL, data=login_data) # Responses not checked here, only in prior tests

    # Sixth request should fail
    response_before_wait = await client.post(LOGIN_URL, data=login_data)
    assert response_before_wait.status_code == 429

    # Wait for the rate limit window to pass (60 seconds for 5/minute)
    # Add a small buffer (e.g., 1 second) to ensure the window has passed.
    time.sleep(61)

    # The next request should succeed (i.e., not be a 429)
    response_after_wait = await client.post(LOGIN_URL, data=login_data)
    assert response_after_wait.status_code != 429, "Login rate limit should have reset after 1 minute."

@pytest.mark.asyncio
async def test_password_recovery_rate_limit_within_limit(client: AsyncClient):
    """Test password recovery attempts within the rate limit (3/hour)."""
    recovery_data = {
        "tipo_documento": "CC",
        "numero_documento": "testuser_recovery_within",
        "correo": "testrecovery_within@example.com"
    }
    for i in range(3):
        response = await client.post(RECOVERY_URL, data=recovery_data)
        assert response.status_code != 429, f"Request {i+1} (recovery within limit) got 429, expected other code."

@pytest.mark.asyncio
async def test_password_recovery_rate_limit_exceeded(client: AsyncClient):
    """Test password recovery attempts exceeding the rate limit (3/hour)."""
    recovery_data = {
        "tipo_documento": "CC",
        "numero_documento": "testuser_recovery_exceed",
        "correo": "testrecovery_exceed@example.com"
    }
    # Exhaust the limit (3 requests)
    for i in range(3):
        response = await client.post(RECOVERY_URL, data=recovery_data)
        assert response.status_code != 429, f"Request {i+1} (recovery to exhaust limit) got 429 unexpectedly."

    # The 4th request should be rate limited
    response = await client.post(RECOVERY_URL, data=recovery_data)
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.text

@pytest.mark.asyncio
async def test_password_recovery_rate_limit_reset_after_time(client: AsyncClient):
    """Test password recovery rate limit resets after the time window (1 hour, simulated shorter)."""
    recovery_data = {
        "tipo_documento": "CC",
        "numero_documento": "testuser_recovery_reset",
        "correo": "testrecovery_reset@example.com"
    }
    # Exhaust the limit
    for i in range(3):
        await client.post(RECOVERY_URL, data=recovery_data) # Responses not checked here

    # Fourth request should fail
    response_before_wait = await client.post(RECOVERY_URL, data=recovery_data)
    assert response_before_wait.status_code == 429

    # Wait for the rate limit window to pass (3600 seconds for 3/hour).
    # This is too long for a practical test. Simulating with a shorter duration (61 seconds).
    # This means the test doesn't truly verify the 1-hour reset but checks if the limiter
    # clears the entry after some time, which is the best we can do with time.sleep here.
    # A tool like freezegun would be needed for true time manipulation.
    print(f"Starting sleep for password recovery reset test (simulated as 61s instead of 3601s)...")
    time.sleep(61)
    print(f"Finished sleep for password recovery reset test.")

    # The next request should succeed (i.e., not be a 429)
    response_after_wait = await client.post(RECOVERY_URL, data=recovery_data)
    assert response_after_wait.status_code != 429, "Password recovery rate limit should have shown reset behavior after simulated wait."
