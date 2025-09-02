import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import DataImportPage from '../../../pages/Import/DataImportPage';
import { usePortfolios } from '../../../hooks/usePortfolios';
import { useCreateImportSession } from '../../../hooks/useImport';

// Mock hooks
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: jest.fn(),
}));
jest.mock('../../../hooks/usePortfolios');
jest.mock('../../../hooks/useImport');

const mockUsePortfolios = usePortfolios as jest.Mock;
const mockUseCreateImportSession = useCreateImportSession as jest.Mock;
const mockNavigate = useNavigate as jest.Mock;

const queryClient = new QueryClient();

const renderComponent = () => {
    return render(
        <QueryClientProvider client={queryClient}>
            <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
                <DataImportPage />
            </MemoryRouter>
        </QueryClientProvider>
    );
};

describe('DataImportPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockUsePortfolios.mockReturnValue({
            data: [{ id: '1', name: 'My Stocks' }],
            isLoading: false,
        });
        mockNavigate.mockReturnValue(jest.fn());
    });

    it('renders the page title and form elements', () => {
        mockUseCreateImportSession.mockReturnValue({ isPending: false, isError: false });
        renderComponent();

        expect(screen.getByText('Import Transactions')).toBeInTheDocument();
        expect(screen.getByLabelText('Select Portfolio')).toBeInTheDocument();
        expect(screen.getByLabelText('Statement Type')).toBeInTheDocument();
        expect(screen.getByText('Upload a file')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Upload and Preview' })).toBeInTheDocument();
    });

    it('disables the submit button until a portfolio and file are selected', () => {
        mockUseCreateImportSession.mockReturnValue({ isPending: false, isError: false });
        renderComponent();

        const submitButton = screen.getByRole('button', { name: 'Upload and Preview' });
        expect(submitButton).toBeDisabled();

        // Select a portfolio
        fireEvent.change(screen.getByLabelText('Select Portfolio'), { target: { value: '1' } });
        expect(submitButton).toBeDisabled();

        // Select a file
        const fileInput = screen.getByLabelText('Upload a file');
        const file = new File(['test'], 'test.csv', { type: 'text/csv' });
        fireEvent.change(fileInput, { target: { files: [file] } });

        // Now button should be enabled
        expect(submitButton).toBeEnabled();
    });

    it('calls the create session mutation on submit and navigates on success', async () => {
        const mockMutate = jest.fn();
        const mockNavigateFn = jest.fn();
        mockUseCreateImportSession.mockReturnValue({
            mutate: mockMutate,
            isSuccess: true,
            data: { id: 'session-123' },
            isPending: false,
        });
        mockNavigate.mockReturnValue(mockNavigateFn);

        renderComponent();

        // Select portfolio, source type and file
        fireEvent.change(screen.getByLabelText('Select Portfolio'), { target: { value: '1' } });
        fireEvent.change(screen.getByLabelText('Statement Type'), { target: { value: 'Zerodha Tradebook' } });
        const file = new File(['test'], 'test.csv', { type: 'text/csv' });
        fireEvent.change(screen.getByLabelText('Upload a file'), { target: { files: [file] } });

        // Submit form
        fireEvent.click(screen.getByRole('button', { name: 'Upload and Preview' }));

        expect(mockMutate).toHaveBeenCalledWith({
            portfolioId: '1',
            source_type: 'Zerodha Tradebook',
            file: file,
        });

        // Check for navigation
        await waitFor(() => {
            expect(mockNavigateFn).toHaveBeenCalledWith('/import/session-123/preview');
        });
    });
});

