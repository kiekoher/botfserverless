import os
import sys
from unittest.mock import Mock

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app"))
import main


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
