-- Create the agents table
CREATE TABLE agents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES auth.users(id) NOT NULL,
    name TEXT NOT NULL,
    base_prompt TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Add comments to the table and columns
COMMENT ON TABLE agents IS 'Stores AI agent configurations for users.';
COMMENT ON COLUMN agents.name IS 'The name of the agent.';
COMMENT ON COLUMN agents.base_prompt IS 'The base prompt or personality of the agent.';
COMMENT ON COLUMN agents.status IS 'The current status of the agent (e.g., active, paused).';

-- Enable Row Level Security (RLS)
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- 1. Policy for SELECT: Users can only see their own agents.
CREATE POLICY "Allow users to see their own agents"
ON agents
FOR SELECT
USING (auth.uid() = user_id);

-- 2. Policy for INSERT: Users can only create agents for themselves.
CREATE POLICY "Allow users to create their own agents"
ON agents
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- 3. Policy for UPDATE: Users can only update their own agents.
CREATE POLICY "Allow users to update their own agents"
ON agents
FOR UPDATE
USING (auth.uid() = user_id);

-- 4. Policy for DELETE: Users can only delete their own agents.
CREATE POLICY "Allow users to delete their own agents"
ON agents
FOR DELETE
USING (auth.uid() = user_id);
