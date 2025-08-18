-- Create the conversations table
CREATE TABLE conversations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id uuid REFERENCES agents(id) ON DELETE CASCADE NOT NULL,
    user_id uuid REFERENCES auth.users(id) NOT NULL, -- The end-user on WhatsApp
    user_message TEXT,
    bot_response TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Add comments
COMMENT ON TABLE conversations IS 'Stores the history of conversations for each agent.';
COMMENT ON COLUMN conversations.agent_id IS 'The agent involved in the conversation.';

-- Add indexes for faster lookups
CREATE INDEX idx_conversations_agent_id ON conversations(agent_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);

-- Enable Row Level Security (RLS)
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can only see conversations for agents they own.
-- This is a bit more complex as it requires a join.
CREATE POLICY "Allow users to see conversations for their own agents"
ON conversations
FOR SELECT
USING (
  EXISTS (
    SELECT 1
    FROM agents
    WHERE agents.id = conversations.agent_id
      AND agents.user_id = auth.uid()
  )
);

-- We are logging conversations from the backend service, which should use the
-- service_role key, so it bypasses RLS for inserts.
-- Therefore, we don't need an INSERT policy for users.
-- For safety, we can add policies to prevent users from manipulating data.
CREATE POLICY "Users cannot insert, update, or delete conversations"
ON conversations
FOR ALL
USING (false)
WITH CHECK (false);
