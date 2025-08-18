import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import MainLayout from '@/components/layout/MainLayout'
import Link from 'next/link';

export default async function DashboardPage() {
  const supabase = createClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) {
    redirect('/login')
  }

  const { data: agents, error } = await supabase
    .from('agents')
    .select('id, name, status')
    .eq('user_id', user.id);

  if (error) {
    console.error('Error fetching agents:', error);
    // Handle error gracefully in the UI
  }

  return (
    <MainLayout>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">My Agents</h1>
        <Link href="/dashboard/agents/new" className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">
          + New Agent
        </Link>
      </div>
      <div className="bg-white p-6 rounded-lg shadow-md">
        {agents && agents.length > 0 ? (
          <ul>
            {agents.map((agent) => (
              <li key={agent.id} className="flex justify-between items-center py-3 border-b last:border-b-0">
                <span className="font-medium">{agent.name}</span>
                <div className="flex items-center space-x-4">
                  <span className={`px-3 py-1 text-sm rounded-full ${
                    agent.status === 'active' ? 'bg-green-200 text-green-800' : 'bg-yellow-200 text-yellow-800'
                  }`}>
                    {agent.status}
                  </span>
                  <Link href={`/dashboard/agents/${agent.id}`} className="text-blue-500 hover:underline">
                    Edit
                  </Link>
                  <Link href={`/dashboard/agents/${agent.id}/conversations`} className="text-gray-500 hover:underline">
                    View Conversations
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p>You haven't created any agents yet.</p>
        )}
      </div>
    </MainLayout>
  )
}
