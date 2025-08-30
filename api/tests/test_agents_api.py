import pytest
from unittest.mock import patch

from main import app
from dependencies import get_current_user_id

# --- Test Data ---
TEST_USER_ID = "test-user-123"
AGENT_CONFIG_PAYLOAD = {
    "name": "Sales Agent X",
    "product_description": "Our product is the best.",
    "base_prompt": "You are a helpful sales assistant."
}

# --- Test Cases ---

@patch("dependencies.supabase_adapter", autospec=True)
def test_upsert_agent_for_current_user_success(mock_supabase_adapter, client):
    """
    Tests successful creation/update of an agent's configuration.
    """
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID

    expected_record = { "id": "new-agent-id", "user_id": TEST_USER_ID, **AGENT_CONFIG_PAYLOAD }
    mock_supabase_adapter.upsert_agent_config.return_value = expected_record

    response = client.post("/api/v1/agents/me", json=AGENT_CONFIG_PAYLOAD)

    assert response.status_code == 201
    assert response.json() == expected_record
    mock_supabase_adapter.upsert_agent_config.assert_called_once_with(
        user_id=TEST_USER_ID,
        name=AGENT_CONFIG_PAYLOAD["name"],
        product_description=AGENT_CONFIG_PAYLOAD["product_description"],
        base_prompt=AGENT_CONFIG_PAYLOAD["base_prompt"]
    )
    app.dependency_overrides = {}


@patch("dependencies.supabase_adapter", autospec=True)
def test_get_agent_for_current_user_success(mock_supabase_adapter, client):
    """
    Tests successful retrieval of an agent's configuration.
    """
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID

    expected_agent_data = { "id": "agent-id-456", "user_id": TEST_USER_ID, **AGENT_CONFIG_PAYLOAD }
    mock_supabase_adapter.get_agent_for_user.return_value = expected_agent_data

    response = client.get("/api/v1/agents/me")

    assert response.status_code == 200
    assert response.json() == expected_agent_data
    mock_supabase_adapter.get_agent_for_user.assert_called_once_with(user_id=TEST_USER_ID)
    app.dependency_overrides = {}


@patch("dependencies.supabase_adapter", autospec=True)
def test_get_agent_for_current_user_not_found(mock_supabase_adapter, client):
    """
    Tests the case where an agent configuration is not found for the user.
    """
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID

    mock_supabase_adapter.get_agent_for_user.return_value = None

    response = client.get("/api/v1/agents/me")

    assert response.status_code == 404
    assert response.json() == {"detail": "Agent configuration not found for this user."}
    mock_supabase_adapter.get_agent_for_user.assert_called_once_with(user_id=TEST_USER_ID)
    app.dependency_overrides = {}
