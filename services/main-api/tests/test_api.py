import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

from app.main import app
from app.dependencies import get_process_chat_message_use_case

# Create a TestClient instance
client = TestClient(app)

# Mock the use case
mock_use_case = MagicMock()
mock_use_case.execute = AsyncMock(return_value="This is a mock response.")


def get_mock_use_case():
    return mock_use_case


# Override the dependency
app.dependency_overrides[get_process_chat_message_use_case] = get_mock_use_case


def test_chat_endpoint_success():
    # Arrange
    payload = {"user_id": "test_user", "query": "Hello", "conversation_history": []}

    # Act
    response = client.post("/api/chat", json=payload)

    # Assert
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["response"] == "This is a mock response."
    assert json_response["user_id"] == "test_user"

    # Verify the mock was called correctly
    mock_use_case.execute.assert_called_once_with(
        user_id="test_user", user_query="Hello", history=[]
    )


def test_chat_endpoint_missing_fields():
    # Arrange
    payload = {
        "user_id": "test_user"
        # "query" is missing
    }

    # Act
    response = client.post("/api/chat", json=payload)

    # Assert
    assert response.status_code == 422  # Unprocessable Entity


# Clean up the override after tests
@pytest.fixture(autouse=True)
def cleanup():
    yield
    app.dependency_overrides = {}
    mock_use_case.execute.reset_mock()
