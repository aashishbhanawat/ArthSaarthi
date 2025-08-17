import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes, useNavigate } from 'react-router-dom';
import ImportPreviewPage from '../../../pages/Import/ImportPreviewPage';
import { useImportSession, useImportSessionPreview, useCommitImportSession } from '../../../hooks/useImport';

// Mock hooks
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: jest.fn(),
}));
jest.mock('../../../hooks/useImport');

const mockUseImportSession = useImportSession as jest.Mock;
const mockUseImportSessionPreview = useImportSessionPreview as jest.Mock;
const mockUseCommitImportSession = useCommitImportSession as jest.Mock;
const mockNavigate = useNavigate as jest.Mock;

const queryClient = new QueryClient();

const renderComponent = (sessionId: string) => {
    return render(
        <QueryClientProvider client={queryClient}>
            <MemoryRouter initialEntries={[`/import/${sessionId}/preview`]}>
                <Routes>
                    <Route path="/import/:sessionId/preview" element={<ImportPreviewPage />} />
                </Routes>
            </MemoryRouter>
        </QueryClientProvider>
    );
};

describe('ImportPreviewPage', () => {
    const mockTransaction = {
        transaction_date: '2023-01-01T00:00:00Z',
        ticker_symbol: 'TEST',
        transaction_type: 'BUY' as const,
        quantity: 10,
        price_per_unit: 100,
        fees: 5,
    };

    beforeEach(() => {
        jest.clearAllMocks();
        mockNavigate.mockReturnValue(jest.fn());
        mockUseImportSession.mockReturnValue({
            data: {
                id: 'session-123',
                file_name: 'test.csv',
                status: 'PARSED',
                portfolio: { name: 'My Stocks' },
                portfolio_id: 'port-1',
            },
            isLoading: false,
        });
        mockUseImportSessionPreview.mockReturnValue({
            data: {
                valid_new: [mockTransaction],
                duplicates: [],
                invalid: [],
                needs_mapping: [],
            },
            isLoading: false,
        });
    });

    it('renders the categorized tables with transaction data', () => {
        mockUseCommitImportSession.mockReturnValue({ isPending: false });
        renderComponent('session-123');

        expect(screen.getByText('Import Preview')).toBeInTheDocument();
        expect(screen.getByText('New Transactions (1)')).toBeInTheDocument();
        expect(screen.getByText('TEST')).toBeInTheDocument();
        expect(screen.getByText('BUY')).toBeInTheDocument();
    });

    it('handles transaction selection and calls the commit mutation with selected data', async () => {
        const mockMutate = jest.fn();
        mockUseCommitImportSession.mockReturnValue({ mutate: mockMutate, isPending: false });

        renderComponent('session-123');

        // Initial state: transaction is selected by default
        let commitButton = await screen.findByRole('button', { name: /Commit 1 Transactions/ });
        let rowCheckbox = (await screen.findAllByRole('checkbox'))[1];
        expect(commitButton).toBeEnabled();
        expect(rowCheckbox).toBeChecked();

        // Deselect the transaction
        fireEvent.click(rowCheckbox);

        // Check state after deselect
        commitButton = await screen.findByRole('button', { name: /Commit 0 Transactions/ });
        rowCheckbox = (await screen.findAllByRole('checkbox'))[1];
        expect(commitButton).toBeDisabled();
        expect(rowCheckbox).not.toBeChecked();

        // Reselect the transaction
        fireEvent.click(rowCheckbox);

        // Check state after reselect
        commitButton = await screen.findByRole('button', { name: /Commit 1 Transactions/ });
        expect(commitButton).toBeEnabled();

        // Click commit
        fireEvent.click(commitButton);

        expect(mockMutate).toHaveBeenCalledWith({
            sessionId: 'session-123',
            portfolioId: 'port-1',
            commitPayload: {
                transactions_to_commit: [mockTransaction],
                aliases_to_create: [],
            },
        });
    });

    it('displays a success message and navigates on successful commit', async () => {
        const mockNavigateFn = jest.fn();
        mockNavigate.mockReturnValue(mockNavigateFn);
        mockUseCommitImportSession.mockReturnValue({
            isSuccess: true,
            isPending: false,
            data: { msg: 'Successfully committed 1 transactions.' },
        });
        renderComponent('session-123');

        expect(screen.getByText(/Successfully committed.*Redirecting to portfolio/)).toBeInTheDocument();

        // Check for navigation after delay
        await waitFor(() => {
            expect(mockNavigateFn).toHaveBeenCalledWith('/portfolios/port-1');
        }, { timeout: 2500 });
    });
});
