import pytest
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from dependencies import check_message_quota, get_current_user_id
from infrastructure.supabase_adapter import SupabaseAdapter

# --- Test Setup ---

# Create a dummy app to test the dependency
app = FastAPI()

# Dummy user ID for tests
TEST_USER_ID = "test-user-123"

# Dummy endpoint that uses the dependency
@app.get("/test-quota")
async def _test_quota_endpoint(_: str = Depends(check_message_quota)):
    return {"status": "ok"}

# Override the get_current_user_id dependency for this test app
async def override_get_current_user_id():
    return TEST_USER_ID

app.dependency_overrides[get_current_user_id] = override_get_current_user_id

# --- Tests ---

@pytest.fixture
def client():
    """Provides a TestClient instance for the test app."""
    with TestClient(app) as test_client:
        yield test_client

@pytest.mark.asyncio
async def test_check_message_quota_has_credits(client, mocker):
    """
    Tests that the check_message_quota dependency allows access
    when the user has sufficient credits.
    """
    # Mock the SupabaseAdapter's method
    mock_supabase_adapter = mocker.patch("dependencies.supabase_adapter", spec=SupabaseAdapter)
    mock_supabase_adapter.has_sufficient_credits.return_value = True

    app.dependency_overrides[mocker.patch("dependencies.get_supabase_adapter")] = lambda: mock_supabase_adapter

    response = client.get("/test-quota")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    mock_supabase_adapter.has_sufficient_credits.assert_called_once_with(TEST_USER_ID)

@pytest.mark.asyncio
async def test_check_message_quota_no_credits(client, mocker):
    """
    Tests that the check_message_quota dependency raises a 429 HTTPException
    when the user has no credits.
    """
    # Mock the SupabaseAdapter's method
    mock_supabase_adapter = mocker.patch("dependencies.supabase_adapter", spec=SupabaseAdapter)
    mock_supabase_adapter.has_sufficient_credits.return_value = False

    app.dependency_overrides[mocker.patch("dependencies.get_supabase_adapter")] = lambda: mock_supabase_adapter

    response = client.get("/test-quota")

    assert response.status_code == 429
    assert "Message credit quota exhausted" in response.json()["detail"]
    mock_supabase_adapter.has_sufficient_credits.assert_called_once_with(TEST_USER_ID)
