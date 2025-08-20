import pytest
from fastapi.testclient import TestClient
from app.main import app

# --- Test Setup ---
# The TestClient allows us to make requests to the FastAPI app in tests.
# It handles the app's lifecycle (startup and shutdown events).
client = TestClient(app)


# --- Test Cases ---
def test_health_check():
    """
    Tests the /health endpoint to ensure the API is running and can connect to Redis.

    This test relies on the Redis service being available, which is handled by
    the docker-compose setup in the CI/CD pipeline.
    """
    response = client.get("/health")

    # Assert that the request was successful
    assert response.status_code == 200

    # Assert that the response body is as expected
    response_json = response.json()
    assert response_json["status"] == "ok"
    assert "redis" in response_json

    # In a test environment with a running Redis, this should be True.
    # If Redis is not available, the endpoint itself is designed to return False,
    # but the overall status is still "ok".
    assert response_json["redis"] is True

# To add more tests, create new functions starting with `test_`.
# For example:
#
# @pytest.mark.skip(reason="Example test, not implemented")
# def test_some_other_endpoint():
#     response = client.post("/some-endpoint", json={"key": "value"})
#     assert response.status_code == 201
#     assert response.json()["message"] == "Created"
