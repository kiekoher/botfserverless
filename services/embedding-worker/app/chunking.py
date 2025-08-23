import logging
import tiktoken

logger = logging.getLogger(__name__)

# Tiktoken for chunking
_tokenizer = tiktoken.get_encoding("cl100k_base")
_MAX_TOKENS_PER_CHUNK = 500  # A reasonable chunk size

def chunk_text(text: str) -> list[str]:
    """Split input text into chunks of at most _MAX_TOKENS_PER_CHUNK tokens."""
    tokens = _tokenizer.encode(text)
    chunks: list[str] = []
    for i in range(0, len(tokens), _MAX_TOKENS_PER_CHUNK):
        chunk_tokens = tokens[i:i + _MAX_TOKENS_PER_CHUNK]
        chunks.append(_tokenizer.decode(chunk_tokens))
    logger.info("Split text into %d chunks.", len(chunks))
    return chunks
