import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.use_cases.process_chat_message import ProcessChatMessage


@pytest.mark.asyncio
async def test_returns_message_if_no_agent():
    router = MagicMock()
    router.route_query = AsyncMock()
    db = MagicMock()
    db.get_agent_for_user = AsyncMock(return_value=None)

    use_case = ProcessChatMessage(router, db)

    result = await use_case.execute("u1", "hi")

    assert result == "I'm sorry, I can't find an agent configured for your account."
    router.route_query.assert_not_called()


@pytest.mark.asyncio
async def test_returns_message_if_agent_paused():
    router = MagicMock()
    router.route_query = AsyncMock()
    db = MagicMock()
    db.get_agent_for_user = AsyncMock(return_value={"id": "a1", "status": "paused"})

    use_case = ProcessChatMessage(router, db)

    result = await use_case.execute("u1", "hi")

    assert result == "This agent is currently paused. Please resume it from the dashboard."
    router.route_query.assert_not_called()


@pytest.mark.asyncio
async def test_successful_flow_routes_and_logs():
    router = MagicMock()
    router.route_query = AsyncMock(return_value="bot")
    db = MagicMock()
    db.get_agent_for_user = AsyncMock(return_value={
        "id": "a1",
        "status": "active",
        "base_prompt": "bp",
        "guardrails": "gr",
    })
    db.get_conversation_history = AsyncMock(return_value=[{"role": "user", "content": "hi"}])
    db.log_conversation = AsyncMock()

    use_case = ProcessChatMessage(router, db)

    result = await use_case.execute("u1", "hi")

    router.route_query.assert_awaited_once_with(
        user_id="u1",
        query="hi",
        history=[{"role": "user", "content": "hi"}],
        task="chat",
        agent_prompt="bp",
        agent_guardrails="gr",
    )
    db.log_conversation.assert_awaited_once_with(
        agent_id="a1",
        user_id="u1",
        user_message="hi",
        bot_response="bot",
    )
    assert result == "bot"
