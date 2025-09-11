import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import TransactionFormModal from '../../../components/Portfolio/TransactionFormModal';
import { Asset } from '../../../types/asset';

// Mocks
const mockCreateTransaction = jest.fn();
const mockCreatePpfAccountWithContribution = jest.fn();
const mockCheckPpfAccount = jest.fn();

jest.mock('../../../hooks/usePortfolios', () => ({
  useCreateTransaction: () => ({
    mutate: mockCreateTransaction,
  }),
  // Mock other hooks from usePortfolios if they are used in the component
  useUpdateTransaction: () => ({ mutate: jest.fn() }),
  useCreateFixedDeposit: () => ({ mutate: jest.fn() }),
}));

jest.mock('../../../hooks/useAssets', () => ({
    useAssetSearch: () => ({ data: [], isLoading: false }),
    useCreateAsset: () => ({ mutate: jest.fn() }),
    useMfSearch: () => ({ data: [], isLoading: false }),
    useCheckPpfAccount: () => mockCheckPpfAccount(),
    useCreatePpfAccountWithContribution: () => ({
        mutate: mockCreatePpfAccountWithContribution,
    }),
}));

const queryClient = new QueryClient();

const mockPpfAsset: Asset = {
    id: 'ppf-asset-1',
    ticker_symbol: 'PPF-123',
    name: 'Test PPF Bank',
    asset_type: 'PPF',
    account_number: 'PPF123456789',
    opening_date: '2022-04-15',
    currency: 'INR',
    isin: null,
    exchange: null,
};

const mockOnClose = jest.fn();

const renderComponent = (ppfExists: boolean) => {
    mockCheckPpfAccount.mockReturnValue({
        data: ppfExists ? mockPpfAsset : undefined,
        isLoading: false,
    });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
         <TransactionFormModal
           isOpen={true}
           onClose={mockOnClose}
           portfolioId="portfolio-1"
         />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('TransactionFormModal for PPF', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should show create form when no PPF account exists', async () => {
    renderComponent(false);

    fireEvent.change(screen.getByLabelText(/asset type/i), { target: { value: 'PPF Account' } });

    await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Create Your PPF Account' })).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText(/institution name/i), { target: { value: 'New PPF Bank' } });
    fireEvent.change(screen.getByLabelText(/account number/i), { target: { value: 'PPF98765' } });
    fireEvent.change(screen.getByLabelText(/opening date/i), { target: { value: '2022-05-20' } });
    fireEvent.change(screen.getByLabelText('Amount (₹)'), { target: { value: '5000' } });
    fireEvent.change(screen.getByLabelText('Date'), { target: { value: '2022-05-21' } });

    fireEvent.click(screen.getByRole('button', { name: /save/i }));

    await waitFor(() => {
        expect(mockCreatePpfAccountWithContribution).toHaveBeenCalledWith(
          expect.objectContaining({
              portfolioId: 'portfolio-1',
              institutionName: 'New PPF Bank',
              accountNumber: 'PPF98765',
              openingDate: '2022-05-20',
              contributionAmount: 5000,
              contributionDate: '2022-05-21',
          }),
          expect.any(Object)
        );
    });
  });

  it('should show contribution form when a PPF account exists', async () => {
    renderComponent(true);

    fireEvent.change(screen.getByLabelText(/asset type/i), { target: { value: 'PPF Account' } });

    await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Existing PPF Account' })).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Amount (₹)'), { target: { value: '10000' } });
    fireEvent.change(screen.getByLabelText('Date'), { target: { value: '2023-08-10' } });
    fireEvent.click(screen.getByRole('button', { name: /save/i }));

    await waitFor(() => {
        expect(mockCreateTransaction).toHaveBeenCalledWith(
          expect.objectContaining({
            portfolioId: 'portfolio-1',
            data: {
              asset_id: mockPpfAsset.id,
              transaction_type: 'CONTRIBUTION',
              quantity: 10000,
              price_per_unit: 1,
              transaction_date: expect.any(String),
            },
          }),
          expect.any(Object)
        );
    });
  });
});