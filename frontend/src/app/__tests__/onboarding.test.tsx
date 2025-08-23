import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import OnboardingPage from '../dashboard/onboarding/page';

jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn().mockReturnValue({ data: { status: 'disconnected' }, isLoading: false }),
  useMutation: jest.fn().mockReturnValue({ mutate: jest.fn(), isPending: false }),
  useQueryClient: jest.fn()
}));

jest.mock('@/services/api', () => ({
  getOnboardingStatus: jest.fn(),
  getWhatsappQrCode: jest.fn()
}));

jest.mock('next/link', () => ({ __esModule: true, default: ({ children }: any) => <div>{children}</div> }));
jest.mock('qrcode.react', () => ({ __esModule: true, default: () => <div>QR</div> }));
jest.mock('next/navigation', () => ({ useRouter: () => ({ push: jest.fn() }) }));

describe('OnboardingPage', () => {
  it('renders heading', () => {
    render(<OnboardingPage />);
    expect(screen.getByText('AI Sales Agent Setup')).toBeInTheDocument();
  });
});
