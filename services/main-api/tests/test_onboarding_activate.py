import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from types import SimpleNamespace

from app.main import app


@pytest.fixture
def client(mocker):
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True
    mock_redis.incr.return_value = 1
    mock_redis.expire.return_value = True
    mocker.patch("app.main.redis_from_url", return_value=mock_redis)
    with TestClient(app) as c:
        yield c


def test_activate_agent(client, mocker, auth_header):
    mock_user = SimpleNamespace(user=SimpleNamespace(id="user-123"))
    mocker.patch(
        "app.dependencies.supabase_adapter.client.auth.get_user",
        return_value=mock_user,
    )
    mock_adapter = mocker.Mock()
    mock_adapter.get_agent_for_user = AsyncMock(return_value={"id": "agent-1"})
    mock_adapter.update_agent_status = AsyncMock(return_value=True)
    mock_adapter.client = SimpleNamespace(auth=SimpleNamespace(get_user=lambda _: mock_user))
    mocker.patch("app.dependencies.supabase_adapter", mock_adapter)

    response = client.post(
        "/api/v1/agent/activate", headers=auth_header("user-123")
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "agent_id": "agent-1"}
    mock_adapter.update_agent_status.assert_called_once_with("agent-1", "active")
