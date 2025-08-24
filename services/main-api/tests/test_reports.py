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


def mock_auth(mocker):
    mock_user = SimpleNamespace(user=SimpleNamespace(id="user-1"))
    mocker.patch(
        "app.dependencies.supabase_adapter.client.auth.get_user",
        return_value=mock_user,
    )


def test_reports_endpoints(client, mocker, auth_header):
    mock_auth(mocker)
    mocker.patch(
        "app.dependencies.supabase_adapter.get_opportunity_briefs",
        AsyncMock(return_value={"user_id": "user-1", "opportunities": []}),
    )
    mocker.patch(
        "app.dependencies.supabase_adapter.get_performance_log",
        AsyncMock(return_value={"user_id": "user-1", "logs": []}),
    )
    mocker.patch(
        "app.dependencies.supabase_adapter.get_executive_summaries",
        AsyncMock(return_value={"user_id": "user-1", "summaries": []}),
    )
    headers = auth_header("user-1")
    for path in [
        "/api/v1/reports/opportunity-briefs",
        "/api/v1/reports/performance-log",
        "/api/v1/reports/executive-summaries",
    ]:
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "user-1"
