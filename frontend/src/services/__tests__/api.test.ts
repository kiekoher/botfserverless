import '@testing-library/jest-dom';

process.env.NEXT_PUBLIC_API_URL = 'http://localhost/api/v1';

jest.mock('@supabase/ssr', () => ({
  createBrowserClient: () => ({
    auth: {
      getSession: jest.fn().mockResolvedValue({ data: { session: { access_token: 'token' } } })
    }
  })
}));

describe('getAgents', () => {
  it('fetches agent list', async () => {
    const { getAgents } = await import('../api');
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

describe('Onboarding API', () => {
  it('fetches onboarding status with auth token', async () => {
    const { getOnboardingStatus } = await import('../api');
    const mockStatus = { status: 'connected' };
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockStatus)
    }) as any;

    const status = await getOnboardingStatus();
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/onboarding/status'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token' })
      })
    );
    expect(status).toEqual(mockStatus);
  });

  it('returns null when QR code not available', async () => {
    const { getWhatsappQrCode } = await import('../api');
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 204,
    }) as any;

    const qr = await getWhatsappQrCode();
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/onboarding/whatsapp-qr'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token' })
      })
    );
    expect(qr).toBeNull();
  });
});
