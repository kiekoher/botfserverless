import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import MainLayout from '@/components/layout/MainLayout'
import Link from 'next/link'

export default function NewAgentPage() {

  async function createAgent(formData: FormData) {
    'use server'

    const supabase = createClient()
    const { data: { user } } = await supabase.auth.getUser()

    if (!user) {
      return redirect('/login')
    }

    const newAgent = {
      user_id: user.id,
      name: formData.get('name') as string,
      base_prompt: formData.get('base_prompt') as string,
      guardrails: formData.get('guardrails') as string,
      status: 'active', // Default status
    }

    const { error } = await supabase.from('agents').insert(newAgent)

    if (error) {
      console.error('Error creating agent:', error)
      // We could add a redirect to an error page or show a toast notification
      redirect('/dashboard?error=Could not create agent')
    } else {
      redirect('/dashboard')
    }
  }

  return (
    <MainLayout>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Create New Agent</h1>
        <Link href="/dashboard" className="px-4 py-2 bg-gray-200 text-black rounded hover:bg-gray-300">
          Cancel
        </Link>
      </div>
      <div className="bg-white p-8 rounded-lg shadow-md">
        <form action={createAgent}>
          <div className="mb-4">
            <label htmlFor="name" className="block text-gray-700 font-bold mb-2">Agent Name</label>
            <input
              type="text"
              id="name"
              name="name"
              className="w-full px-3 py-2 border rounded-lg"
              placeholder="e.g., Customer Support Bot"
              required
            />
          </div>
          <div className="mb-4">
            <label htmlFor="base_prompt" className="block text-gray-700 font-bold mb-2">Base Prompt (Personality)</label>
            <textarea
              id="base_prompt"
              name="base_prompt"
              rows={6}
              className="w-full px-3 py-2 border rounded-lg"
              placeholder="You are a helpful and friendly assistant..."
            />
          </div>
          <div className="mb-6">
            <label htmlFor="guardrails" className="block text-gray-700 font-bold mb-2">Guardrails</label>
            <textarea
              id="guardrails"
              name="guardrails"
              rows={4}
              className="w-full px-3 py-2 border rounded-lg"
              placeholder="e.g., Do not discuss politics. Never use offensive language."
            />
          </div>
          <div className="flex justify-end">
            <button type="submit" className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
              Save Agent
            </button>
          </div>
        </form>
      </div>
    </MainLayout>
  )
}
