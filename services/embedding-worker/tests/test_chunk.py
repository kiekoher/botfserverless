import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app"))
os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test")
os.environ.setdefault("OPENAI_API_KEY", "test")
from main import chunk_text

def test_chunk_text_splits():
    text = "a " * 600
    chunks = chunk_text(text)
    assert len(chunks) > 1
    assert ''.join(chunks).replace(' ', '')[:1] == 'a'
