-- Make sure the vector extension is enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Create the document_chunks table
-- This table will store the text chunks and their embeddings from the documents.
CREATE TABLE document_chunks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id uuid REFERENCES documents(id) ON DELETE CASCADE NOT NULL,
  user_id uuid REFERENCES auth.users(id) NOT NULL,
  content text NOT NULL,
  embedding vector(3072) NOT NULL, -- Corresponds to OpenAI's text-embedding-3-large model
  created_at timestamptz NOT NULL DEFAULT now()
);

-- 2. Add Row Level Security (RLS) to the document_chunks table
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own document chunks.
-- This is crucial for the RAG retrieval process.
CREATE POLICY "Users can read their own document chunks"
  ON document_chunks FOR SELECT
  USING (auth.uid() = user_id);

-- Policy: Allow the service role (used by the embedding-worker) to insert chunks.
-- The service role bypasses RLS, but this makes the intent clear.
CREATE POLICY "Service role can insert document chunks"
  ON document_chunks FOR INSERT
  WITH CHECK (auth.role() = 'service_role');


-- 3. Create an index for faster similarity search
-- We use an IVFFlat index, which is a good starting point for performance.
-- The number of lists is a parameter that might need tuning, but 100 is a reasonable default.
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- 4. Create the RPC function for matching chunks
-- This function is called by the main-api to find relevant context for a user query.
CREATE OR REPLACE FUNCTION match_document_chunks (
  p_user_id uuid,
  query_embedding vector(3072),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id uuid,
  document_id uuid,
  content text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id,
    dc.document_id,
    dc.content,
    1 - (dc.embedding <=> query_embedding) AS similarity
  FROM
    document_chunks AS dc
  WHERE
    dc.user_id = p_user_id AND (1 - (dc.embedding <=> query_embedding)) > match_threshold
  ORDER BY
    similarity DESC
  LIMIT
    match_count;
END;
$$;
