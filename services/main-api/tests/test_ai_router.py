import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.ai_router import AIRouter


@pytest.mark.asyncio
async def test_routes_analysis_to_deepseek_v2():
    gemini = MagicMock()
    gemini.generate_response = AsyncMock()
    deepseek_v2 = MagicMock()
    deepseek_v2.generate_response = AsyncMock()
    deepseek_chat = MagicMock()
    deepseek_chat.generate_response = AsyncMock()
    embedding = MagicMock()
    embedding.supabase_adapter = MagicMock()
    embedding.get_embedding = AsyncMock()

    router = AIRouter(gemini, deepseek_v2, deepseek_chat, embedding)

    await router.route_query("user", "what?", [], "analysis")

    deepseek_v2.generate_response.assert_awaited_once_with("what?", [])
    deepseek_chat.generate_response.assert_not_called()
    gemini.generate_response.assert_not_called()


@pytest.mark.asyncio
async def test_routes_extraction_to_deepseek_chat():
    gemini = MagicMock()
    gemini.generate_response = AsyncMock()
    deepseek_v2 = MagicMock()
    deepseek_v2.generate_response = AsyncMock()
    deepseek_chat = MagicMock()
    deepseek_chat.generate_response = AsyncMock()
    embedding = MagicMock()
    embedding.supabase_adapter = MagicMock()
    embedding.get_embedding = AsyncMock()

    router = AIRouter(gemini, deepseek_v2, deepseek_chat, embedding)

    await router.route_query("user", "info", [], "extraction")

    deepseek_chat.generate_response.assert_awaited_once_with("info", [])
    deepseek_v2.generate_response.assert_not_called()
    gemini.generate_response.assert_not_called()


@pytest.mark.asyncio
async def test_chat_task_runs_rag_pipeline():
    gemini = MagicMock()
    gemini.generate_response = AsyncMock(return_value="resp")
    deepseek_v2 = MagicMock()
    deepseek_v2.generate_response = AsyncMock()
    deepseek_chat = MagicMock()
    deepseek_chat.generate_response = AsyncMock()
    supabase_adapter = MagicMock()
    supabase_adapter.find_relevant_chunks = AsyncMock(return_value=[{"content": "chunk"}])
    embedding = MagicMock()
    embedding.get_embedding = AsyncMock(return_value=[0.1])
    embedding.supabase_adapter = supabase_adapter

    router = AIRouter(gemini, deepseek_v2, deepseek_chat, embedding)

    result = await router.route_query(
        user_id="user",
        query="hello",
        history=[],
        task="chat",
        agent_prompt="hi",
        agent_guardrails="stay safe",
    )

    embedding.get_embedding.assert_awaited_once_with("hello")
    supabase_adapter.find_relevant_chunks.assert_awaited_once()
    gemini.generate_response.assert_awaited_once()
    assert result == "resp"
    args, kwargs = gemini.generate_response.await_args
    assert "chunk" in kwargs["prompt"]
    assert kwargs["history"] == []


@pytest.mark.asyncio
async def test_unknown_task_defaults_to_gemini():
    gemini = MagicMock()
    gemini.generate_response = AsyncMock(return_value="resp")
    deepseek_v2 = MagicMock()
    deepseek_v2.generate_response = AsyncMock()
    deepseek_chat = MagicMock()
    deepseek_chat.generate_response = AsyncMock()
    embedding = MagicMock()
    embedding.supabase_adapter = MagicMock()
    embedding.get_embedding = AsyncMock()

    router = AIRouter(gemini, deepseek_v2, deepseek_chat, embedding)

    await router.route_query("user", "hey", [], "unknown")

    gemini.generate_response.assert_awaited_once_with(prompt="hey", history=[])
    deepseek_v2.generate_response.assert_not_called()
    deepseek_chat.generate_response.assert_not_called()
