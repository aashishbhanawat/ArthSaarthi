import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import CreatePortfolioModal from '../../../components/Portfolio/CreatePortfolioModal';
import { useCreatePortfolio } from '../../../hooks/usePortfolios';

jest.mock('../../../hooks/usePortfolios', () => ({
  useCreatePortfolio: jest.fn(),
}));

const mockUseCreatePortfolio = useCreatePortfolio as jest.Mock;
const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

describe('CreatePortfolioModal', () => {
  const mockOnClose = jest.fn();
  let mockMutate: jest.Mock;

  const queryClient = new QueryClient();

  const renderComponent = (isOpen = true) =>
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <CreatePortfolioModal isOpen={isOpen} onClose={mockOnClose} />
        </MemoryRouter>
      </QueryClientProvider>
    );

  beforeEach(() => {
    mockMutate = jest.fn();
    mockUseCreatePortfolio.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      isSuccess: false,
      isError: false,
      error: null,
      reset: jest.fn(),
    });
    jest.clearAllMocks();
  });

  it('renders the form correctly', () => {
    renderComponent();
    expect(screen.getByRole('heading', { name: /create new portfolio/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/portfolio name/i)).toBeInTheDocument();
  });

  it('calls the create mutation and navigates on successful form submission', async () => {
    mockMutate.mockImplementation((_payload, { onSuccess }) => {
      onSuccess({ id: 123 });
    });
    renderComponent();
    await userEvent.type(screen.getByLabelText(/portfolio name/i), 'My New Portfolio');
    fireEvent.click(screen.getByRole('button', { name: /create/i }));
    await waitFor(() => expect(mockMutate).toHaveBeenCalledWith({ name: 'My New Portfolio' }, expect.any(Object)));
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/portfolios/123'));
  });

  it('calls onClose when the cancel button is clicked', () => {
    renderComponent();
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('does not render when isOpen is false', () => {
    renderComponent(false);
    expect(screen.queryByRole('heading', { name: /create new portfolio/i })).not.toBeInTheDocument();
  });
});