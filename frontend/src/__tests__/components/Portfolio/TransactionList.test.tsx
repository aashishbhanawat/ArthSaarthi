import { render, screen, fireEvent } from '@testing-library/react';
import TransactionList from '../../../components/Portfolio/TransactionList';
import { Transaction } from '../../../types/portfolio';
import { formatDate, formatCurrency } from '../../../utils/formatting';
import { PrivacyProvider } from '../../../context/PrivacyContext';

const mockTransactions: Transaction[] = [
  {
    id: 'tx-1',
    asset_id: 'asset-1',
    portfolio_id: 'p-1',
    transaction_type: 'BUY',
    quantity: 10,
    price_per_unit: 150.75,
    transaction_date: '2023-10-26T10:00:00Z',
    fees: 5,
    asset: { id: 'asset-1', ticker_symbol: 'AAPL', name: 'Apple Inc.', asset_type: 'Stock', currency: 'USD', isin: 'US0378331005', exchange: 'NASDAQ' },
  },
  {
    id: 'tx-2',
    asset_id: 'asset-2',
    portfolio_id: 'p-1',
    transaction_type: 'SELL',
    quantity: 5,
    price_per_unit: 3000.50,
    transaction_date: '2023-10-27T10:00:00Z',
    fees: 10,
    asset: { id: 'asset-2', ticker_symbol: 'GOOGL', name: 'Alphabet Inc.', asset_type: 'Stock', currency: 'USD', isin: 'US02079K3059', exchange: 'NASDAQ' },
  },
];

describe('TransactionList', () => {
  const mockOnEdit = jest.fn();
  const mockOnDelete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders a list of transactions with correct data and formatting', () => {
    render(
      <PrivacyProvider>
        <TransactionList transactions={mockTransactions} onEdit={mockOnEdit} onDelete={mockOnDelete} />
      </PrivacyProvider>
    );

    // Check for headers
    expect(screen.getByRole('columnheader', { name: /date/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /asset/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /actions/i })).toBeInTheDocument();

    // Check for first transaction's data
    const firstTx = mockTransactions[0];
    expect(screen.getByText(formatDate(firstTx.transaction_date))).toBeInTheDocument();
    expect(screen.getByText(firstTx.asset.ticker_symbol)).toBeInTheDocument();
    expect(screen.getByText(formatCurrency(Number(firstTx.price_per_unit), firstTx.asset.currency))).toBeInTheDocument();
    expect(screen.getByText(firstTx.transaction_type)).toBeInTheDocument();
  });

  it('calls onEdit with the correct transaction when the edit button is clicked', () => {
    render(
      <PrivacyProvider>
        <TransactionList transactions={mockTransactions} onEdit={mockOnEdit} onDelete={mockOnDelete} />
      </PrivacyProvider>
    );
    
    const editButton = screen.getByRole('button', { name: /edit transaction for AAPL/i });
    fireEvent.click(editButton);

    expect(mockOnEdit).toHaveBeenCalledTimes(1);
    expect(mockOnEdit).toHaveBeenCalledWith(mockTransactions[0]);
  });

  it('calls onDelete with the correct transaction when the delete button is clicked', () => {
    render(
      <PrivacyProvider>
        <TransactionList transactions={mockTransactions} onEdit={mockOnEdit} onDelete={mockOnDelete} />
      </PrivacyProvider>
    );
    
    const deleteButton = screen.getByRole('button', { name: /delete transaction for GOOGL/i });
    fireEvent.click(deleteButton);

    expect(mockOnDelete).toHaveBeenCalledTimes(1);
    expect(mockOnDelete).toHaveBeenCalledWith(mockTransactions[1]);
  });

  it('renders a message when there are no transactions', () => {
    render(
      <PrivacyProvider>
        <TransactionList transactions={[]} onEdit={mockOnEdit} onDelete={mockOnDelete} />
      </PrivacyProvider>
    );
    expect(screen.getByText(/no transactions found/i)).toBeInTheDocument();
  });
});