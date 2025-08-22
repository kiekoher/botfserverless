// In a real application, this would come from the Supabase auth context
const MOCK_USER_ID = "a1b2c3d4-e5f6-7890-1234-567890abcdef";

export const authenticatedFetch = async (url: string, options: RequestInit = {}) => {
  const headers = new Headers(options.headers);
  headers.append("X-User-ID", MOCK_USER_ID);

  if (options.body) {
    headers.append("Content-Type", "application/json");
  }

  const newOptions: RequestInit = {
    ...options,
    headers,
  };

  const response = await fetch(url, newOptions);

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorBody.detail || 'An unknown error occurred');
  }

  // Handle 204 No Content case
  if (response.status === 204) {
    return null;
  }

  return response.json();
};

export const authenticatedFormDataFetch = async (url: string, formData: FormData) => {
  const MOCK_USER_ID = "a1b2c3d4-e5f6-7890-1234-567890abcdef";
  const headers = new Headers();
  headers.append("X-User-ID", MOCK_USER_ID);

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorBody.detail || 'An unknown error occurred');
  }

  return response.json();
};
