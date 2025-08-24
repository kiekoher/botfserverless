-- Add a JSONB column to store flexible agent configurations, like prompts, models, etc.
ALTER TABLE public.agents
ADD COLUMN config JSONB NOT NULL DEFAULT '{}'::jsonb;

-- Add a comment to describe the purpose of the new column.
COMMENT ON COLUMN public.agents.config IS 'Flexible JSONB field to store agent-specific configurations like system prompts, model parameters, etc.';
