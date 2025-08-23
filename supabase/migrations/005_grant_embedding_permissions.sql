-- This policy allows the embedding-worker, using the anonymous key, to insert new documents.
-- The RLS (Row Level Security) must be enabled on the 'documents' table for this to take effect.
-- We assume RLS is already enabled on the table as per Supabase best practices.

-- First, drop any existing insert policy for the anon role on the documents table to avoid conflicts.
DROP POLICY IF EXISTS "Allow anon key to insert new documents" ON public.documents;

-- Create the specific policy for the embedding-worker.
-- This policy allows any user with the 'anon' role to insert into the documents table.
-- It's a broad policy, but necessary for the worker which operates without a specific user context.
-- The security is maintained by the fact that this key should only be known to the backend services.
CREATE POLICY "Allow anon key to insert new documents"
ON public.documents FOR INSERT
TO anon
WITH CHECK (true);

-- It is also important to ensure that authenticated users can still read their own documents.
-- This policy should already exist from previous migrations, but we include it here for completeness
-- and to ensure it is correctly defined.

-- Drop the policy if it exists, to prevent errors on re-running migrations.
DROP POLICY IF EXISTS "Allow authenticated users to read their own documents" ON public.documents;

-- Create the policy for authenticated users to read documents associated with their agent_id.
CREATE POLICY "Allow authenticated users to read their own documents"
ON public.documents FOR SELECT
TO authenticated
USING (auth.uid() = agent_id);
