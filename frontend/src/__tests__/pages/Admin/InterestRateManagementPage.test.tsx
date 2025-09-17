import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { ToastProvider } from '../../../context/ToastContext';
import InterestRateManagementPage from '../../../pages/Admin/InterestRateManagementPage';
import * as useInterestRatesHook from '../../../hooks/useInterestRates';
import { HistoricalInterestRate } from '../../../types/interestRate';
import InterestRateTable from '../../../components/Admin/InterestRateTable';

const queryClient = new QueryClient();

const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>{ui}</ToastProvider>
    </QueryClientProvider>
  );
};

jest.mock('../../../hooks/useInterestRates');
jest.mock('../../../components/Admin/InterestRateTable', () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const React = require('react');
    // Return a Jest mock function so we can change its implementation for specific tests
    return jest.fn(() => React.createElement('div', null, 'InterestRateTable'));
});
jest.mock('../../../components/Admin/InterestRateFormModal', () => {
    return function DummyInterestRateFormModal({ isOpen }: { isOpen: boolean }) {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const React = require('react');
        return isOpen ? React.createElement('div', null, 'InterestRateFormModal') : null;
    };
});
jest.mock('../../../components/common/DeleteConfirmationModal', () => {
    return {
        DeleteConfirmationModal: function DummyDeleteConfirmationModal({ isOpen }: { isOpen: boolean }) {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const React = require('react');
        return isOpen ? React.createElement('div', null, 'DeleteConfirmationModal') : null;
    }};
});

const mockedUseInterestRates = useInterestRatesHook.useInterestRates as jest.Mock;

const mockRates: HistoricalInterestRate[] = [
  { id: '1', scheme_name: 'PPF', start_date: '2023-04-01', end_date: '2024-03-31', rate: 7.1 },
];

describe('InterestRateManagementPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state correctly', () => {
    mockedUseInterestRates.mockReturnValue({ isLoading: true, isError: false, data: [] });
    renderWithProviders(<InterestRateManagementPage />);
    expect(screen.getByText('Loading interest rates...')).toBeInTheDocument();
  });

  it('renders error state correctly', () => {
    mockedUseInterestRates.mockReturnValue({ isLoading: false, isError: true, data: [] });
    renderWithProviders(<InterestRateManagementPage />);
    expect(screen.getByText('Error fetching interest rates.')).toBeInTheDocument();
  });

  it('renders the page with data correctly', () => {
    mockedUseInterestRates.mockReturnValue({ isLoading: false, isError: false, data: mockRates });
    renderWithProviders(<InterestRateManagementPage />);
    expect(screen.getByText('Interest Rate Management')).toBeInTheDocument();
    expect(screen.getByText('InterestRateTable')).toBeInTheDocument();
    expect(screen.queryByText('InterestRateFormModal')).not.toBeInTheDocument();
  });

  it('opens the create modal when "Add New Rate" button is clicked', async () => {
    mockedUseInterestRates.mockReturnValue({ isLoading: false, isError: false, data: mockRates });
    renderWithProviders(<InterestRateManagementPage />);
    fireEvent.click(screen.getByRole('button', { name: /Add New Rate/i }));
    await waitFor(() => {
      expect(screen.getByText('InterestRateFormModal')).toBeInTheDocument();
    });
  });

  it('opens the delete modal when onDelete is called from the table', async () => {
    mockedUseInterestRates.mockReturnValue({ isLoading: false, isError: false, data: mockRates });
    // This is a simplified way to test the interaction without a real table
    (InterestRateTable as jest.Mock).mockImplementationOnce(({ onDelete }: { onDelete: (rate: HistoricalInterestRate) => void }) => {
      return React.createElement('button', { onClick: () => onDelete(mockRates[0]) }, 'Delete');
    });

    renderWithProviders(<InterestRateManagementPage />);
    fireEvent.click(screen.getByText('Delete'));
    await waitFor(() => {
      expect(screen.getByText('DeleteConfirmationModal')).toBeInTheDocument();
    });
  });
});