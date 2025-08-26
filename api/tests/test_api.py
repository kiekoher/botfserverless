import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# The import path is now relative to the `api` directory
from main import app

# --- Fixtures ---

@pytest.fixture
def client():
    """Provides a TestClient instance for the tests."""
    with TestClient(app) as test_client:
        yield test_client


# --- Test Cases ---

def test_simple_health_check(client):
    """Tests the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_deep_health_check_db_ok(client, mocker):
    """Tests the /health/deep endpoint with a successful DB connection."""
    mock_rpc = AsyncMock()
    mock_rpc.execute.return_value = None
    mock_client = mocker.MagicMock()
    mock_client.rpc.return_value = mock_rpc

    mocker.patch.object(app.state.supabase_adapter, 'client', new=mock_client)

    response = client.get("/health/deep")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": True}


def test_deep_health_check_db_fail(client, mocker):
    """Tests the /health/deep endpoint with a failed DB connection."""
    mock_rpc = AsyncMock()
    mock_rpc.execute.side_effect = Exception("DB Connection Error")
    mock_client = mocker.MagicMock()
    mock_client.rpc.return_value = mock_rpc

    mocker.patch.object(app.state.supabase_adapter, 'client', new=mock_client)

    response = client.get("/health/deep")
    assert response.status_code == 503
    assert response.json() == {
        "status": "unhealthy",
        "database": False,
        "errors": ["Database: DB Connection Error"],
    }


@patch("main.cloudflare_queue_adapter.publish_message", new_callable=AsyncMock)
def test_handle_whatsapp_message_success(mock_publish, client):
    """Tests the WhatsApp message handler endpoint for a successful case."""
    payload = {
        "userId": "12345",
        "userName": "Test User",
        "chatId": "12345",
        "timestamp": "1678886400",
        "body": "Hello, world!",
    }
    response = client.post("/api/v1/messages/whatsapp", json=payload)

    assert response.status_code == 202
    assert response.json() == {"status": "accepted"}
    mock_publish.assert_called_once_with(payload)


@patch("main.cloudflare_queue_adapter.publish_message", new_callable=AsyncMock)
def test_handle_whatsapp_message_queue_fails(mock_publish, client):
    """Tests the WhatsApp message handler when the queue publish fails."""
    mock_publish.side_effect = Exception("Queue is down")
    payload = {"userId": "12345", "body": "test"}

    response = client.post("/api/v1/messages/whatsapp", json=payload)

    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to process message"}


def test_handle_whatsapp_message_invalid_payload(client):
    """Tests the WhatsApp message handler with an invalid payload."""
    payload = {"body": "This is missing a userId"}
    response = client.post("/api/v1/messages/whatsapp", json=payload)

    assert response.status_code == 400
    assert response.json() == {"detail": "Missing 'userId' in payload"}
