import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# --- Add app directory to path to allow for imports ---
import os
import importlib.util

# Dynamically load the transcription worker's main module to avoid package name collisions
spec = importlib.util.spec_from_file_location(
    "transcription_worker_main",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../app/main.py")),
)
transcription_worker = importlib.util.module_from_spec(spec)

# Since main.py runs code on import, mock external dependencies before executing
mock_boto3 = MagicMock()
mock_whisper = MagicMock()

with patch.dict(
    "sys.modules",
    {
        "boto3": mock_boto3,
        "faster_whisper": mock_whisper,
        "pydub": MagicMock(),
    },
):
    spec.loader.exec_module(transcription_worker)

@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset mocks before each test."""
    mock_boto3.reset_mock()
    mock_whisper.reset_mock()
    transcription_worker.s3_client = None
    transcription_worker.whisper_model = None


@pytest.fixture
def mock_redis_client():
    """Fixture for a mocked async Redis client."""
    client = AsyncMock()
    client.xadd = AsyncMock()
    client.xack = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_process_message_no_media(mock_redis_client):
    """
    Tests if a message without media is processed correctly,
    simply forwarding the body text.
    """
    message_id = "12345-0"
    message_data = {
        "userId": "user1",
        "chatId": "chat1",
        "timestamp": "1678886400",
        "body": "Hello, world!",
        "mediaKey": None,
    }

    success = await transcription_worker.process_message_with_retry(
        mock_redis_client, message_id, message_data
    )

    assert success is True
    # Verify it was added to the output stream
    mock_redis_client.xadd.assert_called_once()
    # Check the payload sent to the next stream
    output_payload = mock_redis_client.xadd.call_args[0][1]
    assert output_payload["body"] == "Hello, world!"
    assert output_payload["transcribed"] == "false"


@pytest.mark.asyncio
@patch.object(
    transcription_worker,
    "download_audio_from_r2_sync",
    return_value="/tmp/fake_audio.ogg",
)
@patch.object(
    transcription_worker,
    "transcribe_audio_sync",
    return_value="This is a test transcription.",
)
async def test_process_message_with_media(
    mock_transcribe, mock_download, mock_redis_client
):
    """
    Tests the full pipeline for a message with media:
    download -> transcribe -> forward.
    """
    message_id = "12345-1"
    message_data = {
        "userId": "user2",
        "chatId": "chat2",
        "timestamp": "1678886401",
        "body": "",
        "mediaKey": "audio/some-key.ogg",
    }

    # We need to use asyncio.to_thread in the test to simulate how it's called
    async def to_thread_side_effect(func, *args, **kwargs):
        if func == transcription_worker.download_audio_from_r2_sync:
            return mock_download(*args, **kwargs)
        if func == transcription_worker.transcribe_audio_sync:
            return mock_transcribe(*args, **kwargs)
        return await asyncio.get_event_loop().run_in_executor(None, func, *args, **kwargs)


    with patch("asyncio.to_thread", side_effect=to_thread_side_effect):
        success = await transcription_worker.process_message_with_retry(
            mock_redis_client, message_id, message_data
        )

    assert success is True
    mock_download.assert_called_once_with("audio/some-key.ogg")
    mock_transcribe.assert_called_once_with("/tmp/fake_audio.ogg")

    # Verify the transcribed text is in the output payload
    mock_redis_client.xadd.assert_called_once()
    output_payload = mock_redis_client.xadd.call_args[0][1]
    assert output_payload["body"] == "This is a test transcription."
    assert output_payload["transcribed"] == "true"


@pytest.mark.asyncio
@patch.object(
    transcription_worker,
    "download_audio_from_r2_sync",
    side_effect=Exception("S3 Download Failed"),
)
async def test_process_message_download_fails_and_retries(mock_download, mock_redis_client):
    """
    Tests that a message processing fails, retries, and moves to DLQ
    if a download error persists.
    """
    message_id = "12345-2"
    message_data = {"mediaKey": "audio/failing-key.ogg"}

    # Mock asyncio.sleep to avoid waiting in tests
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
         # We need to use asyncio.to_thread in the test to simulate how it's called
        async def to_thread_side_effect(func, *args, **kwargs):
            if func == transcription_worker.download_audio_from_r2_sync:
                return mock_download(*args, **kwargs)
            return await asyncio.get_event_loop().run_in_executor(None, func, *args, **kwargs)

        with patch("asyncio.to_thread", side_effect=to_thread_side_effect):
            success = await transcription_worker.process_message_with_retry(
                mock_redis_client, message_id, message_data
            )


    assert success is False
    # Check that it was tried MAX_RETRIES times
    assert mock_download.call_count == transcription_worker.MAX_RETRIES
    # Check that it tried to sleep between retries
    assert mock_sleep.call_count == transcription_worker.MAX_RETRIES - 1

    # Verify it was NOT added to the main output stream
    mock_redis_client.xadd.assert_not_called()


def test_download_audio_sync():
    """Tests the synchronous download helper."""
    # Setup
    mock_s3 = MagicMock()
    mock_s3.download_file = MagicMock()
    transcription_worker.s3_client = mock_s3

    with patch("tempfile.mkstemp", return_value=(123, "/tmp/tempfile.ogg")), \
         patch("os.close"):
        local_path = transcription_worker.download_audio_from_r2_sync("my-key")

    assert local_path == "/tmp/tempfile.ogg"
    mock_s3.download_file.assert_called_once_with(
        transcription_worker.R2_BUCKET_NAME, "my-key", "/tmp/tempfile.ogg"
    )

@patch("os.path.exists", return_value=True)
@patch("os.remove")
def test_transcribe_audio_sync(mock_remove, mock_exists):
    """Tests the synchronous transcription helper."""
    # Setup
    mock_model = MagicMock()
    # Mock the return value of transcribe to be a tuple (segments, info)
    mock_segment = MagicMock()
    mock_segment.text = "hello world"
    mock_info = MagicMock()
    mock_info.language = "en"
    mock_info.language_probability = 0.99
    mock_model.transcribe.return_value = ([mock_segment], mock_info)
    transcription_worker.whisper_model = mock_model

    mock_audio_segment = MagicMock()
    mock_audio_segment.export.return_value = None

    with patch("pydub.AudioSegment.from_file", return_value=mock_audio_segment):
        result = transcription_worker.transcribe_audio_sync("/tmp/audio.ogg")

    assert result == "hello world"
    mock_model.transcribe.assert_called_once()
    # Check that cleanup was attempted on both ogg and wav files
    assert mock_remove.call_count == 2
