import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import PortfolioDetailPage from '../../../pages/Portfolio/PortfolioDetailPage';
import * as portfolioHooks from '../../../hooks/usePortfolios';
import { Portfolio } from '../../../types/portfolio';

jest.mock('../../../hooks/usePortfolios');
const mockedPortfolioHooks = portfolioHooks as jest.Mocked<typeof portfolioHooks>;

jest.mock('../../../components/Portfolio/TransactionFormModal', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require('react');
  return ({ onClose, transactionToEdit }: any) =>
    React.createElement('div', { 'data-testid': 'transaction-form-modal' },
      React.createElement('h2', { role: 'heading' }, transactionToEdit ? 'Edit Transaction' : 'Add Transaction'),
      React.createElement('button', { onClick: onClose }, 'Close')
    );
});

jest.mock('../../../components/common/DeleteConfirmationModal.tsx', () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const React = require('react');
    const MockedModal = ({ onConfirm, onClose, title }: any) =>
        React.createElement('div', { 'data-testid': 'delete-confirmation-modal' },
            React.createElement('h2', { role: 'heading' }, title),
            React.createElement('button', { onClick: onConfirm }, 'Confirm Delete'),
            React.createElement('button', { onClick: onClose }, 'Cancel')
        );
    // The component uses a NAMED import, so the mock must return an object with that named export.
    return { DeleteConfirmationModal: MockedModal };
});

const queryClient = new QueryClient();

const mockPortfolio: Portfolio = {
  id: 'p-1',
  name: 'Tech Investments',
  description: 'My tech stock portfolio',
  transactions: [
    {
      id: 'tx-1',
      asset_id: 'asset-1',
      portfolio_id: 'p-1',
      transaction_type: 'BUY',
      quantity: 10,
      price_per_unit: 150,
      transaction_date: '2025-07-25T12:00:00Z',
      fees: 5,
      asset: { id: 'asset-1', ticker_symbol: 'AAPL', name: 'Apple Inc.', asset_type: 'Stock', currency: 'USD' },
    },
  ],
};

const renderComponent = () => {
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/portfolios/p-1']} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route path="/portfolios/:id" element={<PortfolioDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('PortfolioDetailPage', () => {
  const mockDeleteTransactionMutate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockedPortfolioHooks.usePortfolio.mockReturnValue({ data: mockPortfolio, isLoading: false, isError: false } as any);
    mockedPortfolioHooks.usePortfolioAnalytics.mockReturnValue({ data: {}, isLoading: false, isError: false } as any);
    mockedPortfolioHooks.useDeleteTransaction.mockReturnValue({ mutate: mockDeleteTransactionMutate, isPending: false } as any);
  });

  it('opens the add transaction modal when the button is clicked', async () => {
    renderComponent();
    await userEvent.click(screen.getByRole('button', { name: /add transaction/i }));
    await waitFor(() => {
      expect(screen.getByTestId('transaction-form-modal')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /add transaction/i })).toBeInTheDocument();
    });
  });

  it('opens the edit transaction modal when an edit button is clicked', async () => {
    renderComponent();
    // Use the specific aria-label for robustness
    await userEvent.click(screen.getByRole('button', { name: /edit transaction for AAPL/i }));
    await waitFor(() => {
      expect(screen.getByTestId('transaction-form-modal')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /edit transaction/i })).toBeInTheDocument();
    });
  });

  it('opens the delete confirmation modal and calls delete mutation on confirm', async () => {
    renderComponent();
    // Use the specific aria-label for robustness
    await userEvent.click(screen.getByRole('button', { name: /delete transaction for AAPL/i }));

    await waitFor(() => expect(screen.getByTestId('delete-confirmation-modal')).toBeInTheDocument());
    expect(screen.getByRole('heading', { name: /delete transaction/i })).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /confirm delete/i }));

    await waitFor(() => {
      expect(mockDeleteTransactionMutate).toHaveBeenCalledWith(
        { portfolioId: 'p-1', transactionId: 'tx-1' },
        expect.any(Object)
      );
    });
  });
});