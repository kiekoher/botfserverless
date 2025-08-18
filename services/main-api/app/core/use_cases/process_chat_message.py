from app.core.ai_router import AIRouter
from app.infrastructure.supabase_adapter import SupabaseAdapter


class ProcessChatMessage:
    def __init__(
        self, router: AIRouter, db_adapter: SupabaseAdapter
    ):
        self.router = router
        self.db_adapter = db_adapter

    async def execute(self, user_id: str, user_query: str, history: list) -> str:
        """
        Orchestrates the processing of a user's chat message using the AI Router.
        """
        # 1. Get the agent configuration for the user
        agent = self.db_adapter.get_agent_for_user(user_id)

        if not agent:
            return "I'm sorry, I can't find an agent configured for your account."

        if agent.get('status') == 'paused':
            return "This agent is currently paused. Please resume it from the dashboard."

        # 2. Route the query to the appropriate AI model
        # We can pass the agent's specific config to the router
        bot_response = await self.router.route_query(
            query=user_query,
            history=history,
            agent_prompt=agent.get('base_prompt'),
            agent_guardrails=agent.get('guardrails')
        )

        # 3. Log the conversation
        try:
            self.db_adapter.log_conversation(
                agent_id=agent['id'],
                user_id=user_id,
                user_message=user_query,
                bot_response=bot_response
            )
            print(f"Logged conversation for user {user_id} with agent {agent['id']}.")
        except Exception as e:
            print(f"Error logging conversation for user {user_id}: {e}")

        return bot_response
