import { createBrowserClient } from '@supabase/ssr'

// Initialize a Supabase client
const supabase = createBrowserClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// Define the base URL for our main API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost/api';

// --- Helper function to get the auth token ---
async function getAuthToken() {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    throw new Error("User is not authenticated.");
  }
  return session.access_token;
}

// --- API functions ---

/**
 * A generic fetch function with authentication
 */
async function fetchFromApi(path: string, options: RequestInit = {}) {
  const token = await getAuthToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...options.headers,
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    // A more robust error handling would be better here
    const errorData = await response.json().catch(() => ({ message: response.statusText }));
    throw new Error(errorData.message || 'An unknown error occurred');
  }

  return response.json();
}

// --- Agent-related API functions ---

export const getAgents = async () => {
  return fetchFromApi('/agents');
};

export const getAgentById = async (agentId: string) => {
  return fetchFromApi(`/agents/${agentId}`);
};

export interface CreateAgentPayload {
    name: string;
    // Add other fields for agent creation here
}

export const createAgent = async (payload: CreateAgentPayload) => {
  return fetchFromApi('/agents', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
};

// --- Add other API functions for knowledge, config, etc. as they are built ---
