import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app"))
from chunking import chunk_text

def test_chunk_text_splits():
    text = "a " * 600
    chunks = chunk_text(text)
    assert len(chunks) > 1
    assert ''.join(chunks).replace(' ', '')[:1] == 'a'
