import pytest
from fastapi.testclient import TestClient
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.main import app


@pytest.fixture
def client(mocker):
    mock_redis = mocker.AsyncMock()
    mock_redis.ping.return_value = True
    mocker.patch("app.main.redis_from_url", return_value=mock_redis)
    with TestClient(app) as test_client:
        yield test_client


def test_quality_metrics(client, mocker, auth_header):
    mock_user = SimpleNamespace(user=SimpleNamespace(id="user-1"))
    mocker.patch(
        "app.dependencies.supabase_adapter.client.auth.get_user",
        return_value=mock_user,
    )
    mocker.patch(
        "app.dependencies.supabase_adapter.get_quality_metrics",
        AsyncMock(return_value={
            "user_id": "user-1",
            "conversations_reviewed": 5,
            "avg_response_time_sec": 1,
            "csat": 0.9,
        }),
    )
    response = client.get(
        "/api/v1/quality/metrics", headers=auth_header("user-1")
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "user-1"
    assert body["conversations_reviewed"] == 5
