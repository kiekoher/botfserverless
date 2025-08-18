import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import MainLayout from '@/components/layout/MainLayout'
import Link from 'next/link';

// Function to format timestamp
const formatTimestamp = (dateString: string) => {
  const options: Intl.DateTimeFormatOptions = {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  };
  return new Date(dateString).toLocaleString('en-US', options);
};

export default async function ConversationsPage({ params }: { params: { id: string } }) {
  const supabase = createClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) {
    redirect('/login')
  }

  // Fetch agent details to display the name
  const { data: agent, error: agentError } = await supabase
    .from('agents')
    .select('name')
    .eq('id', params.id)
    .single();

  if (agentError || !agent) {
    return <MainLayout><p>Agent not found.</p></MainLayout>
  }

  // Fetch conversations for the agent
  const { data: conversations, error } = await supabase
    .from('conversations')
    .select('*')
    .eq('agent_id', params.id)
    .order('created_at', { ascending: true });

  if (error) {
    console.error('Error fetching conversations:', error);
    // Handle error gracefully
  }

  return (
    <MainLayout>
      <div className="mb-8">
        <Link href="/dashboard" className="text-blue-500 hover:underline">
          &larr; Back to Agents
        </Link>
        <h1 className="text-3xl font-bold mt-2">Conversation History for: {agent.name}</h1>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="space-y-6">
          {conversations && conversations.length > 0 ? (
            conversations.map((convo) => (
              <div key={convo.id}>
                {/* User Message */}
                <div className="flex justify-end">
                  <div className="bg-blue-100 text-gray-800 p-4 rounded-lg max-w-lg">
                    <p>{convo.user_message}</p>
                    <p className="text-xs text-gray-500 mt-2 text-right">{formatTimestamp(convo.created_at)}</p>
                  </div>
                </div>
                {/* Bot Response */}
                <div className="flex justify-start mt-2">
                  <div className="bg-gray-200 text-gray-800 p-4 rounded-lg max-w-lg">
                    <p>{convo.bot_response}</p>
                    <p className="text-xs text-gray-500 mt-2 text-left">{formatTimestamp(convo.created_at)}</p>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <p className="text-center text-gray-500">No conversations found for this agent.</p>
          )}
        </div>
      </div>
    </MainLayout>
  )
}
