import '@testing-library/jest-dom';
import { getAgents } from '../api';

jest.mock('@supabase/ssr', () => ({
  createBrowserClient: () => ({
    auth: {
      getSession: jest.fn().mockResolvedValue({ data: { session: { access_token: 'token' } } })
    }
  })
}));

describe('getAgents', () => {
  it('fetches agent list', async () => {
    const mockAgents = [{ id: '1', name: 'Agent 1', status: 'active' }];
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockAgents)
    }) as any;

    const agents = await getAgents();
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/agents'), expect.any(Object));
    expect(agents).toEqual(mockAgents);
  });
});
