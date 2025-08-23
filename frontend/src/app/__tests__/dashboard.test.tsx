import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import KnowledgePage from '../dashboard/knowledge/page';

jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn().mockReturnValue({ data: [], isLoading: false, error: null }),
  useMutation: jest.fn().mockReturnValue({ mutate: jest.fn(), isPending: false }),
  useQueryClient: jest.fn()
}));

jest.mock('react-dropzone', () => ({
  useDropzone: () => ({ getRootProps: () => ({}), getInputProps: () => ({}), isDragActive: false })
}));

jest.mock('../../services/api', () => ({
  getDocuments: jest.fn(),
  uploadDocument: jest.fn()
}));

describe('KnowledgePage', () => {
  it('renders heading', () => {
    render(<KnowledgePage />);
    expect(screen.getByText('Knowledge Base')).toBeInTheDocument();
  });
});
