import { render, screen, fireEvent } from '@testing-library/react';
import TransactionHistoryTable from '../../../components/Transactions/TransactionHistoryTable';
import { Transaction } from '../../../types/portfolio';
import { PrivacyProvider } from '../../../context/PrivacyContext';
import { formatDate } from '../../../utils/formatting';

// Mock TransactionDetailsModal avoiding JSX scope issues
jest.mock('../../../components/Transactions/TransactionDetailsModal', () => {
  return function MockTransactionDetailsModal({ transaction, onClose }: { transaction: any, onClose: any }) {
    const React = require('react');
    return React.createElement('div', { 'data-testid': 'transaction-details-modal' },
      React.createElement('button', { onClick: onClose }, 'Close'),
      React.createElement('div', {}, transaction.id)
    );
  };
});

const mockTransactions: Transaction[] = [
  {
    id: 'tx-1',
    portfolio_id: 'p-1',
    asset_id: 'asset-1',
    transaction_type: 'BUY',
    quantity: 10,
    price_per_unit: 100,
    transaction_date: '2023-01-01T00:00:00Z',
    fees: 0,
    asset: {
      id: 'asset-1',
      ticker_symbol: 'AAPL',
      name: 'Apple Inc.',
      asset_type: 'EQUITY',
      currency: 'USD',
    },
    details: {
      fx_rate: 80,
    },
  },
  {
    id: 'tx-2',
    portfolio_id: 'p-1',
    asset_id: 'asset-2',
    transaction_type: 'SELL',
    quantity: 5,
    price_per_unit: 150,
    transaction_date: '2023-01-02T00:00:00Z',
    fees: 0,
    asset: {
      id: 'asset-2',
      ticker_symbol: 'GOOGL',
      name: 'Alphabet Inc.',
      asset_type: 'EQUITY',
      currency: 'USD',
    },
    // No details, so no info button
  },
];

describe('TransactionHistoryTable', () => {
  const mockOnEdit = jest.fn();
  const mockOnDelete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders transactions correctly', () => {
    render(
      <PrivacyProvider>
        <TransactionHistoryTable
          transactions={mockTransactions}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      </PrivacyProvider>
    );

    expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
    expect(screen.getByText('Alphabet Inc.')).toBeInTheDocument();
  });

  it('renders the details button (InformationCircleIcon) for transactions with details', () => {
    render(
      <PrivacyProvider>
        <TransactionHistoryTable
          transactions={mockTransactions}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      </PrivacyProvider>
    );

    // The first transaction has details, so it should have the button
    const detailsButton = screen.getByLabelText('View details');
    expect(detailsButton).toBeInTheDocument();

    // Check if it opens the modal
    fireEvent.click(detailsButton);
    expect(screen.getByTestId('transaction-details-modal')).toBeInTheDocument();
  });

  it('does not render the details button for transactions without details', () => {
    render(
      <PrivacyProvider>
        <TransactionHistoryTable
          transactions={[mockTransactions[1]]} // Only the one without details
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      </PrivacyProvider>
    );

    const detailsButton = screen.queryByLabelText('View details');
    expect(detailsButton).not.toBeInTheDocument();
  });

  it('calls onEdit when Edit button is clicked', () => {
    render(
      <PrivacyProvider>
        <TransactionHistoryTable
          transactions={[mockTransactions[0]]}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      </PrivacyProvider>
    );

    // There might be multiple "Edit" buttons if we rendered multiple transactions,
    // but here we render one. However, the component renders "Edit" text buttons.
    const editButton = screen.getByText('Edit');
    fireEvent.click(editButton);

    expect(mockOnEdit).toHaveBeenCalledWith(mockTransactions[0]);
  });

  it('calls onDelete when Delete button is clicked', () => {
    render(
      <PrivacyProvider>
        <TransactionHistoryTable
          transactions={[mockTransactions[0]]}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      </PrivacyProvider>
    );

    const deleteButton = screen.getByText('Delete');
    fireEvent.click(deleteButton);

    expect(mockOnDelete).toHaveBeenCalledWith(mockTransactions[0]);
  });
});
