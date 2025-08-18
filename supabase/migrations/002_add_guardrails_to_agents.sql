-- Add a new column to the agents table for guardrails
ALTER TABLE agents
ADD COLUMN guardrails TEXT;

-- Add a comment to the new column
COMMENT ON COLUMN agents.guardrails IS 'A set of rules or forbidden topics for the agent.';
