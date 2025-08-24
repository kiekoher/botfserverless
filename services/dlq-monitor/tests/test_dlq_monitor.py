import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "app"))
import main


@pytest.mark.asyncio
async def test_setup_creates_group():
    redis = AsyncMock()
    await main.setup(redis)
    redis.xgroup_create.assert_awaited_with(
        main.DLQ_STREAM, main.CONSUMER_GROUP, id="0", mkstream=True
    )


@pytest.mark.asyncio
async def test_touch_healthcheck_file(tmp_path, monkeypatch):
    file_path = tmp_path / "healthcheck"
    monkeypatch.setattr(main, "HEALTHCHECK_FILE", file_path)
    await main.touch_healthcheck_file()
    assert file_path.exists()


@pytest.mark.asyncio
async def test_handle_messages_processes_and_ack(monkeypatch):
    redis = AsyncMock()
    message_id = "1-0"
    message = {"error_service": "svc", "foo": "bar"}

    called = False

    async def xreadgroup(*args, **kwargs):
        nonlocal called
        if not called:
            called = True
            return [(main.DLQ_STREAM, [(message_id, message)])]
        await asyncio.sleep(1)

    redis.xreadgroup.side_effect = xreadgroup
    async def cancel_after_delay():
        await asyncio.sleep(0.1)
        raise asyncio.CancelledError

    task = asyncio.create_task(main.handle_messages(redis))
    canceller = asyncio.create_task(cancel_after_delay())
    with pytest.raises(asyncio.CancelledError):
        await asyncio.gather(task, canceller)
    redis.xack.assert_awaited_with(main.DLQ_STREAM, main.CONSUMER_GROUP, message_id)
