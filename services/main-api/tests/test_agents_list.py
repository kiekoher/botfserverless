import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from types import SimpleNamespace

from app.main import app


@pytest.fixture
def mock_redis_ping(mocker):
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True
    mock_redis.incr.return_value = 1
    mock_redis.expire.return_value = True
    mocker.patch("app.main.redis_from_url", return_value=mock_redis)
    return mock_redis


@pytest.fixture
def client(mock_redis_ping):
    with TestClient(app) as test_client:
        yield test_client


def test_list_agents_for_user(client, mocker, auth_header):
    mock_user = SimpleNamespace(user=SimpleNamespace(id="user-123"))
    mocker.patch(
        "app.dependencies.supabase_adapter.client.auth.get_user",
        return_value=mock_user,
    )
    mock_adapter = mocker.Mock()
    mock_adapter.list_agents_for_user = AsyncMock(return_value=[
        {"id": "1", "name": "Agent 1", "status": "active"}
    ])
    mock_adapter.client = SimpleNamespace(auth=SimpleNamespace(get_user=lambda _: mock_user))
    mocker.patch("app.dependencies.supabase_adapter", mock_adapter)

    response = client.get(
        "/api/v1/agents", headers=auth_header("user-123")
    )
    assert response.status_code == 200
    assert response.json() == [
        {"id": "1", "name": "Agent 1", "status": "active"}
    ]
    mock_adapter.list_agents_for_user.assert_called_once_with(user_id="user-123")
