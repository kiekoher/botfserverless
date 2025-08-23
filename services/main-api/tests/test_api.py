import pytest
from fastapi.testclient import TestClient
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from app.main import app

# --- Mocks and Fixtures ---

@pytest.fixture
def mock_redis_ping(mocker):
    """Mocks the redis ping to always succeed."""
    # We patch 'redis_from_url' in the 'app.main' module where it is used.
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True
    mocker.patch("app.main.redis_from_url", return_value=mock_redis)
    return mock_redis

@pytest.fixture
def client(mock_redis_ping):
    """
    Provides a TestClient instance for the tests, ensuring that the
    Redis dependency is mocked before the app starts.
    """
    # The TestClient will automatically handle the app's lifespan,
    # and because we've patched redis_from_url, it will use our mock.
    with TestClient(app) as test_client:
        yield test_client


# --- Test Cases ---

def test_health_check_redis_ok(client):
    """
    Tests the /health endpoint simulating a successful Redis connection.
    """
    # The client fixture ensures the app is started with a mocked Redis.
    response = client.get("/health")

    # Assert that the request was successful
    assert response.status_code == 200

    # Assert that the response body shows a successful Redis connection
    response_json = response.json()
    assert response_json["status"] == "ok"
    assert response_json["redis"] is True


def test_health_check_redis_fail(mocker, client):
    """
    Tests the /health endpoint simulating a failed Redis connection.
    """
    # We can further modify the mock for this specific test
    mock_redis = AsyncMock()
    mock_redis.ping.side_effect = ConnectionError("Failed to connect")
    mocker.patch("app.main.redis_from_url", return_value=mock_redis)

    # We need a new client to pick up the new mock
    with TestClient(app) as new_client:
        response = new_client.get("/health")

        # Assert that the request was successful (the endpoint should handle the error)
        assert response.status_code == 200

        # Assert that the response body shows a failed Redis connection
        response_json = response.json()
        assert response_json["status"] == "ok"
        assert response_json["redis"] is False

# To add more tests, create new functions starting with `test_`.
# For example:
#
# @pytest.mark.skip(reason="Example test, not implemented")
# def test_some_other_endpoint():
#     response = client.post("/some-endpoint", json={"key": "value"})
#     assert response.status_code == 201
#     assert response.json()["message"] == "Created"
