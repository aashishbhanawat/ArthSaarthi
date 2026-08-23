import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CapitalLossLedgerModal } from './CapitalLossLedgerModal';
import * as hooks from '../../hooks/useCapitalGains';

// Mock hook
jest.mock('../../hooks/useCapitalGains', () => ({
  ...jest.requireActual('../../hooks/useCapitalGains'),
  useCapitalLossLedger: jest.fn(),
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

describe('CapitalLossLedgerModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('does not render when isOpen is false', () => {
    (hooks.useCapitalLossLedger as jest.Mock).mockReturnValue({
      data: [],
      isLoading: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <CapitalLossLedgerModal isOpen={false} onClose={jest.fn()} currentFy="2025-26" />
      </QueryClientProvider>
    );

    expect(screen.queryByText(/Carry-Forward Capital Loss Ledger/i)).not.toBeInTheDocument();
  });

  it('renders loss ledger modal and displays entries when isOpen is true', () => {
    (hooks.useCapitalLossLedger as jest.Mock).mockReturnValue({
      data: [
        {
          id: 'ledger-1',
          user_id: 'user-1',
          financial_year: '2023-24',
          assessment_year: '2024-25',
          stcl_amount: 15000,
          ltcl_amount: 0,
          is_itr_filed_on_time: true,
          years_remaining: 6,
          is_expired: false,
        },
      ],
      isLoading: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <CapitalLossLedgerModal isOpen={true} onClose={jest.fn()} currentFy="2025-26" />
      </QueryClientProvider>
    );

    expect(screen.getByText(/Carry-Forward Capital Loss Ledger/i)).toBeInTheDocument();
    expect(screen.getByText(/FY 2023-24/i)).toBeInTheDocument();
    expect(screen.getByText(/AY 2024-25/i)).toBeInTheDocument();
    expect(screen.getByText(/6 AY Remaining/i)).toBeInTheDocument();
  });
});
