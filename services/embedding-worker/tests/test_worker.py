import importlib.util
import os
import sys
from unittest.mock import Mock, patch

os.environ.setdefault("R2_ENDPOINT_URL", "http://example.com")
os.environ.setdefault("R2_ACCESS_KEY_ID", "key")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "secret")
os.environ.setdefault("R2_BUCKET_NAME", "bucket")

spec = importlib.util.spec_from_file_location(
    "embedding_worker_main",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../app/main.py")),
)
main = importlib.util.module_from_spec(spec)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../app")))

mock_redis = Mock()
mock_boto3 = Mock()
mock_openai = Mock(return_value=Mock())
mock_supabase_module = Mock(create_client=Mock(return_value=Mock()), Client=Mock)
mock_pypdf2 = Mock(PdfReader=Mock())

with patch.dict(
    "sys.modules",
    {
        "redis": Mock(Redis=Mock(return_value=mock_redis)),
        "boto3": mock_boto3,
        "openai": Mock(OpenAI=mock_openai, RateLimitError=Exception),
        "PyPDF2": mock_pypdf2,
        "supabase": mock_supabase_module,
    },
):
    spec.loader.exec_module(main)


def test_process_document_success(monkeypatch):
    message = {
        "document_id": "doc1",
        "storage_path": "file.txt",
        "user_id": "user1",
    }

    monkeypatch.setattr(main, "get_text_from_storage", lambda path: "hello world")
    monkeypatch.setattr(main, "chunk_text", lambda text: ["chunk1", "chunk2"])
    monkeypatch.setattr(main, "get_embeddings", lambda texts: [[0.1], [0.2]])

    insert_mock = Mock()
    insert_mock.execute.return_value = None
    table_mock = Mock(return_value=Mock(insert=Mock(return_value=insert_mock)))
    supabase_mock = Mock(table=table_mock)
    monkeypatch.setattr(main, "supabase", supabase_mock)

    xadd_mock = Mock()
    monkeypatch.setattr(main.redis_client, "xadd", xadd_mock)

    status_calls = []
    monkeypatch.setattr(
        main,
        "update_document_status",
        lambda doc_id, status: status_calls.append((doc_id, status)),
    )

    assert main.process_document(message)
    assert status_calls[0] == ("doc1", "processing")
    assert status_calls[-1] == ("doc1", "completed")
    table_mock.assert_called_with("document_chunks")
    xadd_mock.assert_not_called()


def test_process_document_failure(monkeypatch):
    message = {
        "document_id": "doc1",
        "storage_path": "file.txt",
        "user_id": "user1",
    }

    def raise_error(_):
        raise ValueError("boom")

    monkeypatch.setattr(main, "get_text_from_storage", raise_error)
    xadd_mock = Mock()
    monkeypatch.setattr(main.redis_client, "xadd", xadd_mock)

    status_calls = []
    monkeypatch.setattr(
        main,
        "update_document_status",
        lambda doc_id, status: status_calls.append((doc_id, status)),
    )

    assert not main.process_document(message)
    assert status_calls[-1] == ("doc1", "failed")
    xadd_mock.assert_called_once()
