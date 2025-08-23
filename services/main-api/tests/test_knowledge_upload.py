import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

os.environ.setdefault("R2_ENDPOINT_URL", "http://example.com")
os.environ.setdefault("R2_ACCESS_KEY_ID", "key")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "secret")
os.environ.setdefault("R2_BUCKET_NAME", "bucket")

from app.main import app
from app.dependencies import get_current_user_id
import app.api.v1.knowledge as knowledge


@pytest.fixture(autouse=True)
def override_user_id():
    app.dependency_overrides[get_current_user_id] = lambda: "user123"
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_redis(mocker):
    mock_redis = AsyncMock()
    mocker.patch("app.main.redis_from_url", return_value=mock_redis)
    return mock_redis


@pytest.fixture
def client(mock_redis):
    with TestClient(app) as c:
        yield c


def _setup_state(supabase_adapter, redis_client):
    import app.dependencies as deps

    deps.supabase_adapter = supabase_adapter
    app.state.redis = redis_client


def test_cleanup_when_document_creation_fails(client, mocker):
    supabase = MagicMock()
    supabase.get_agent_for_user = AsyncMock(return_value={"id": "agent1"})
    supabase.create_document_record = AsyncMock(return_value=None)
    redis_client = AsyncMock()
    _setup_state(supabase, redis_client)

    s3_mock = MagicMock()
    mocker.patch.object(knowledge, "s3_client", s3_mock)
    mocker.patch.object(knowledge, "R2_BUCKET_NAME", "bucket")

    resp = client.post(
        "/api/v1/knowledge/upload",
        files={"file": ("test.txt", b"data")},
    )
    assert resp.status_code == 500
    s3_mock.delete_object.assert_called_once()


def test_cleanup_when_redis_publish_fails(client, mocker):
    supabase = MagicMock()
    supabase.get_agent_for_user = AsyncMock(return_value={"id": "agent1"})
    supabase.create_document_record = AsyncMock(return_value={"id": "doc1"})
    supabase.delete_document = AsyncMock(return_value=True)
    redis_client = AsyncMock()
    redis_client.xadd.side_effect = Exception("boom")
    _setup_state(supabase, redis_client)

    s3_mock = MagicMock()
    mocker.patch.object(knowledge, "s3_client", s3_mock)
    mocker.patch.object(knowledge, "R2_BUCKET_NAME", "bucket")

    resp = client.post(
        "/api/v1/knowledge/upload",
        files={"file": ("test.txt", b"data")},
    )
    assert resp.status_code == 500
    s3_mock.delete_object.assert_called_once()
    supabase.delete_document.assert_called_once_with("doc1")
