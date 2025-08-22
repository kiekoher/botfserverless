"use client";

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAgentConfig, saveAgentConfig, AgentConfig } from '@/services/api';

export default function ConfigPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [productDescription, setProductDescription] = useState('');
  const [basePrompt, setBasePrompt] = useState('');
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Fetch existing agent configuration
  const { data: existingConfig, isLoading, error } = useQuery<AgentConfig>({
    queryKey: ['agentConfig'],
    queryFn: getAgentConfig,
    retry: (failureCount, error) => {
      // Don't retry on 404, it just means no config exists yet
      return error.message !== 'Agent configuration not found for this user.';
    }
  });

  // Populate form when existing data is loaded
  useEffect(() => {
    if (existingConfig) {
      setName(existingConfig.name || '');
      setProductDescription(existingConfig.product_description || '');
      setBasePrompt(existingConfig.base_prompt || '');
    }
  }, [existingConfig]);

  // Mutation for saving the configuration
  const { mutate, isPending } = useMutation<AgentConfig, Error, AgentConfig>({
    mutationFn: saveAgentConfig,
    onSuccess: (data) => {
      // Invalidate and refetch the query to get fresh data
      queryClient.invalidateQueries({ queryKey: ['agentConfig'] });
      setNotification({ message: 'Configuration saved successfully!', type: 'success' });
      setTimeout(() => setNotification(null), 3000);
    },
    onError: (error) => {
      setNotification({ message: `Error: ${error.message}`, type: 'error' });
      setTimeout(() => setNotification(null), 3000);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutate({ name, product_description: productDescription, base_prompt: basePrompt });
  };

  if (isLoading) {
    return <div className="p-8"><p>Loading configuration...</p></div>;
  }

  if (error && error.message !== 'Agent configuration not found for this user.') {
     return <div className="p-8"><p className="text-red-500">Error loading configuration: {error.message}</p></div>;
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Agent Personality</h1>
      <p className="text-gray-600 mb-8">
        Define the core characteristics of your AI sales agent. This information will guide its tone, behavior, and responses.
      </p>

      <form onSubmit={handleSubmit} className="space-y-8 bg-white p-8 rounded-lg shadow-md">
        <div>
          <label htmlFor="name" className="block text-lg font-semibold text-gray-700 mb-2">
            Agent Name
          </label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
            placeholder="e.g., SalesBot 3000"
            required
          />
          <p className="text-sm text-gray-500 mt-2">The name your agent will use to introduce itself.</p>
        </div>

        <div>
          <label htmlFor="productDescription" className="block text-lg font-semibold text-gray-700 mb-2">
            Product or Service Description
          </label>
          <textarea
            id="productDescription"
            value={productDescription}
            onChange={(e) => setProductDescription(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
            rows={3}
            placeholder="e.g., We sell a subscription-based service for cloud monitoring..."
            required
          />
          <p className="text-sm text-gray-500 mt-2">A clear and concise description of what you are selling.</p>
        </div>

        <div>
          <label htmlFor="basePrompt" className="block text-lg font-semibold text-gray-700 mb-2">
            System Prompt (Personality & Instructions)
          </label>
          <textarea
            id="basePrompt"
            value={basePrompt}
            onChange={(e) => setBasePrompt(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
            rows={12}
            placeholder="You are a friendly and professional sales assistant. Your goal is to qualify leads..."
            required
          />
          <p className="text-sm text-gray-500 mt-2">The core instructions for your agent. Define its tone, style, objectives, and constraints.</p>
        </div>

        <div className="flex items-center justify-end">
          {notification && (
            <div className={`mr-4 text-sm ${notification.type === 'success' ? 'text-green-600' : 'text-red-600'}`}>
              {notification.message}
            </div>
          )}
          <button
            type="submit"
            disabled={isPending}
            className="px-8 py-3 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isPending ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </form>
    </div>
  );
}
