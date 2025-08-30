import pytest
from unittest.mock import AsyncMock, MagicMock
from infrastructure.supabase_adapter import SupabaseAdapter

USER_ID = "test-user-id"

@pytest.fixture
def adapter():
    """Fixture to create a SupabaseAdapter with a mocked _execute method."""
    # Bypass the __init__ that requires env vars
    adapter = SupabaseAdapter.__new__(SupabaseAdapter)
    adapter.client = MagicMock()  # The client itself can be a simple mock
    adapter._execute = AsyncMock() # This is the method we will control
    return adapter

@pytest.mark.asyncio
async def test_has_sufficient_credits_true(adapter: SupabaseAdapter):
    """Tests has_sufficient_credits when user has credits."""
    adapter._execute.return_value = MagicMock(data={"message_credits": 10})

    result = await adapter.has_sufficient_credits(USER_ID)

    assert result is True
    adapter._execute.assert_called_once()

@pytest.mark.asyncio
async def test_has_sufficient_credits_false(adapter: SupabaseAdapter):
    """Tests has_sufficient_credits when user has zero credits."""
    adapter._execute.return_value = MagicMock(data={"message_credits": 0})

    result = await adapter.has_sufficient_credits(USER_ID)

    assert result is False

@pytest.mark.asyncio
async def test_has_sufficient_credits_no_subscription(adapter: SupabaseAdapter):
    """Tests has_sufficient_credits when user has no subscription record."""
    adapter._execute.return_value = MagicMock(data=None)

    result = await adapter.has_sufficient_credits(USER_ID)

    assert result is False

@pytest.mark.asyncio
async def test_has_sufficient_credits_db_error(adapter: SupabaseAdapter):
    """Tests has_sufficient_credits when the DB call fails."""
    adapter._execute.side_effect = Exception("Database connection failed")

    result = await adapter.has_sufficient_credits(USER_ID)

    assert result is False

@pytest.mark.asyncio
async def test_decrement_message_credits_success(adapter: SupabaseAdapter):
    """Tests successful credit decrement via RPC call."""
    adapter._execute.return_value = MagicMock(data=[{"success": True, "new_credits": 9}])

    result = await adapter.decrement_message_credits(USER_ID)

    assert result is True
    adapter._execute.assert_called_once()
    # We can also inspect the call to _execute if needed, but it's complex
    # a, k = adapter._execute.call_args
    # assert k == {}
    # assert a[0].method == "rpc"


@pytest.mark.asyncio
async def test_decrement_message_credits_failure(adapter: SupabaseAdapter):
    """Tests failed credit decrement (e.g., insufficient funds)."""
    adapter._execute.return_value = MagicMock(data=[{"success": False}])

    result = await adapter.decrement_message_credits(USER_ID)

    assert result is False

@pytest.mark.asyncio
async def test_decrement_message_credits_rpc_error(adapter: SupabaseAdapter):
    """Tests credit decrement when the RPC call itself fails."""
    adapter._execute.side_effect = Exception("RPC Network Error")

    result = await adapter.decrement_message_credits(USER_ID)

    assert result is False
