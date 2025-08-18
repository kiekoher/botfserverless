'use client'

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import MainLayout from '@/components/layout/MainLayout';

// Define the type for our agent data
type Agent = {
  id?: string;
  name: string;
  base_prompt: string;
  status: 'active' | 'paused';
  guardrails?: string;
};

export default function AgentDetailPage({ params }: { params: { id:string } }) {
  const router = useRouter();
  const supabase = createClient();
  const isNew = params.id === 'new';

  const [agent, setAgent] = useState<Agent>({ name: '', base_prompt: '', status: 'active', guardrails: '' });
  const [loading, setLoading] = useState(!isNew);

  useEffect(() => {
    if (!isNew) {
      const fetchAgent = async () => {
        const { data, error } = await supabase
          .from('agents')
          .select('*')
          .eq('id', params.id)
          .single();

        if (error || !data) {
          console.error('Error fetching agent:', error);
          alert('Failed to fetch agent data. Redirecting to dashboard.');
          router.push('/dashboard');
        } else {
          setAgent(data);
        }
        setLoading(false);
      };
      fetchAgent();
    }
  }, [params.id, isNew, router, supabase]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();

    let error;
    if (isNew) {
      // Create new agent
      ({ error } = await supabase.from('agents').insert({ ...agent }));
    } else {
      // Update existing agent
      ({ error } = await supabase.from('agents').update({ ...agent }).eq('id', params.id));
    }

    if (error) {
      alert(`Error saving agent: ${error.message}`);
    } else {
      alert('Agent saved successfully!');
      router.push('/dashboard');
      router.refresh(); // To reflect changes on the dashboard list
    }
  };

  const handleStatusToggle = async () => {
    const newStatus = agent.status === 'active' ? 'paused' : 'active';
    setAgent({ ...agent, status: newStatus });

    const { error } = await supabase
      .from('agents')
      .update({ status: newStatus })
      .eq('id', params.id);

    if (error) {
      alert(`Error updating status: ${error.message}`);
      // Revert state if update fails
      setAgent({ ...agent, status: agent.status });
    } else {
      alert(`Agent is now ${newStatus}.`);
    }
  };

  if (loading) {
    return <MainLayout><p>Loading agent...</p></MainLayout>;
  }

  return (
    <MainLayout>
      <h1 className="text-3xl font-bold mb-8">{isNew ? 'Create New Agent' : `Edit Agent: ${agent.name}`}</h1>

      <form onSubmit={handleSave} className="bg-white p-8 rounded-lg shadow-md">
        {/* Emergency Pause */}
        {!isNew && (
          <div className="flex items-center justify-between p-4 bg-yellow-100 border-l-4 border-yellow-500 rounded-md mb-8">
            <div>
              <h3 className="font-bold text-yellow-800">Emergency Pause Mode</h3>
              <p className="text-sm text-yellow-700">
                Instantly pause or resume all interactions for this agent.
              </p>
            </div>
            <button
              type="button"
              onClick={handleStatusToggle}
              className={`px-6 py-2 rounded-full font-semibold text-white ${
                agent.status === 'active' ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'
              }`}
            >
              {agent.status === 'active' ? 'PAUSE' : 'RESUME'}
            </button>
          </div>
        )}

        <div className="mb-6">
          <label htmlFor="name" className="block text-lg font-medium mb-2">Agent Name</label>
          <input
            id="name"
            type="text"
            value={agent.name}
            onChange={(e) => setAgent({ ...agent, name: e.target.value })}
            className="w-full p-3 border rounded-md"
            placeholder="e.g., Sales Assistant"
            required
          />
        </div>

        <div className="mb-6">
          <label htmlFor="base_prompt" className="block text-lg font-medium mb-2">Base Prompt</label>
          <textarea
            id="base_prompt"
            value={agent.base_prompt}
            onChange={(e) => setAgent({ ...agent, base_prompt: e.target.value })}
            className="w-full p-3 border rounded-md h-48"
            placeholder="Describe the agent's personality, role, and instructions..."
            required
          />
        </div>

        <div className="mb-6">
          <label htmlFor="guardrails" className="block text-lg font-medium mb-2">Guardrails</label>
          <textarea
            id="guardrails"
            value={agent.guardrails || ''}
            onChange={(e) => setAgent({ ...agent, guardrails: e.target.value })}
            className="w-full p-3 border rounded-md h-32"
            placeholder="Define forbidden topics or rules for the agent. e.g., 'Do not discuss politics.'"
          />
        </div>

        {/* RAG Document Upload - Placeholder */}
        <div className="mb-8">
          <label className="block text-lg font-medium mb-2">Knowledge Base (RAG)</label>
          <div className="p-6 border-2 border-dashed rounded-md text-center">
            <p className="text-gray-500">Document upload functionality coming soon.</p>
          </div>
        </div>

        <div className="flex justify-end">
          <button type="button" onClick={() => router.back()} className="px-6 py-2 mr-4 bg-gray-200 rounded hover:bg-gray-300">
            Cancel
          </button>
          <button type="submit" className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
            Save Agent
          </button>
        </div>
      </form>
    </MainLayout>
  );
}
