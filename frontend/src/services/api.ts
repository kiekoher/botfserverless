import { createBrowserClient } from '@supabase/ssr'

// Initialize a Supabase client
const supabase = createBrowserClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// Define the base URL for our main API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;
if (!API_BASE_URL) {
  throw new Error('NEXT_PUBLIC_API_URL is required');
}

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
async function fetchFromApi(path: string, options: RequestInit = {}, retry = true) {
  const token = await getAuthToken();
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        ...options.headers,
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });

    if (response.status === 401 && retry) {
      await supabase.auth.refreshSession();
      return fetchFromApi(path, options, false);
    }

    if (response.status === 204) {
      return null;
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(errorData.message || 'An unknown error occurred');
    }

    return response.json();
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Network error';
    throw new Error(message);
  }
}

// --- Agent-related API functions ---

export interface Agent {
  id: string;
  name: string;
  status: string;
}

export const getAgents = async (): Promise<Agent[]> => {
  return fetchFromApi('/agents');
};

export const createAgent = async (payload: AgentConfig) => {
  return fetchFromApi('/agents/me', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
};

// --- Agent configuration ---

export interface AgentConfig {
  name: string;
  product_description: string;
  base_prompt: string;
}

export const getAgentConfig = async (): Promise<AgentConfig> => {
  return fetchFromApi('/agents/me');
};

export const saveAgentConfig = async (
  config: AgentConfig,
): Promise<AgentConfig> => {
  return fetchFromApi('/agents/me', {
    method: 'POST',
    body: JSON.stringify(config),
  });
};

// --- Knowledge documents ---

export interface Document {
  id: string;
  file_name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
}

export const getDocuments = async (): Promise<Document[]> => {
  return fetchFromApi('/knowledge/documents');
};

export const uploadDocument = async (file: File) => {
  const token = await getAuthToken();
  const formData = new FormData();
  formData.append('file', file);
  const response = await fetch(`${API_BASE_URL}/knowledge/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => ({ message: response.statusText }));
    throw new Error(errorData.message || 'An unknown error occurred');
  }

  return response.json();
};

// --- Onboarding ---

export interface OnboardingStatus {
  status: 'disconnected' | 'connected' | 'loading';
}

export interface QrCodeResponse {
  qr_code: string;
}

export const getOnboardingStatus = async (): Promise<OnboardingStatus> => {
  return fetchFromApi('/onboarding/status');
};

export const getWhatsappQrCode = async (): Promise<QrCodeResponse | null> => {
  return fetchFromApi('/onboarding/whatsapp-qr');
};

export const activateAgent = async () => {
  return fetchFromApi('/agent/activate', { method: 'POST' });
};

// --- Quality metrics ---
export interface QualityMetric {
  id: string;
  name: string;
  value: number;
}

export const getQualityMetrics = async (): Promise<QualityMetric[]> => {
  return fetchFromApi('/quality/metrics');
};

// --- Billing ---
export interface BillingInfo {
  plan: string;
  status: string;
}

export const getBillingInfo = async (): Promise<BillingInfo> => {
  return fetchFromApi('/billing/info');
};

// --- Reports ---
export interface OpportunityBrief {
  id: string;
  summary: string;
}

export const getOpportunityBriefs = async (): Promise<OpportunityBrief[]> => {
  return fetchFromApi('/reports/opportunity-briefs');
};

export interface PerformanceLogEntry {
  id: string;
  event: string;
  created_at: string;
}

export const getPerformanceLog = async (): Promise<PerformanceLogEntry[]> => {
  return fetchFromApi('/reports/performance-log');
};

export interface ExecutiveSummary {
  id: string;
  title: string;
  created_at: string;
}

export const getExecutiveSummaries = async (): Promise<ExecutiveSummary[]> => {
  return fetchFromApi('/reports/executive-summaries');
};
