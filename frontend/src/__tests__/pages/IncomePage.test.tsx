import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import IncomePage from '../../pages/IncomePage';
import * as useIncomeHooks from '../../hooks/useIncome';
import { PrivacyProvider } from '../../context/PrivacyContext';

jest.mock('../../hooks/useIncome');

const mockUseIncomeSources = useIncomeHooks.useIncomeSources as jest.Mock;
const mockUseIncomeEntries = useIncomeHooks.useIncomeEntries as jest.Mock;
const mockUseIncomeSummary = useIncomeHooks.useIncomeSummary as jest.Mock;
const mockUseCreateIncomeSource = useIncomeHooks.useCreateIncomeSource as jest.Mock;
const mockUseUpdateIncomeSource = useIncomeHooks.useUpdateIncomeSource as jest.Mock;
const mockUseDeleteIncomeSource = useIncomeHooks.useDeleteIncomeSource as jest.Mock;
const mockUseCreateIncomeEntry = useIncomeHooks.useCreateIncomeEntry as jest.Mock;
const mockUseUpdateIncomeEntry = useIncomeHooks.useUpdateIncomeEntry as jest.Mock;
const mockUseDeleteIncomeEntry = useIncomeHooks.useDeleteIncomeEntry as jest.Mock;

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const renderComponent = () => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <PrivacyProvider>
        <IncomePage />
      </PrivacyProvider>
    </QueryClientProvider>
  );
};

describe('IncomePage Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    mockUseIncomeSources.mockReturnValue({
      data: [
        { id: 'src1', user_id: 'u1', name: 'Primary Tech Salary', category: 'SALARY', payer_name: 'Acme Corp' },
      ],
      isLoading: false,
    });

    mockUseIncomeEntries.mockReturnValue({
      data: [
        {
          id: 'ent1',
          user_id: 'u1',
          source_id: 'src1',
          financial_year: '2025-2026',
          entry_date: '2025-05-31',
          gross_amount: 150000,
          tds_amount: 15000,
          net_amount: 135000,
          notes: 'May Salary',
          source_name: 'Primary Tech Salary',
          source_category: 'SALARY',
        },
      ],
      isLoading: false,
    });

    mockUseIncomeSummary.mockReturnValue({
      data: {
        financial_year: '2025-2026',
        total_gross: 150000,
        total_tds: 15000,
        total_net: 135000,
        source_breakdown: [],
      },
      isLoading: false,
    });

    mockUseCreateIncomeSource.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseUpdateIncomeSource.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseDeleteIncomeSource.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseCreateIncomeEntry.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseUpdateIncomeEntry.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseDeleteIncomeEntry.mockReturnValue({ mutateAsync: jest.fn() });
  });

  test('renders page title, summary cards, source cards, and entry rows', () => {
    renderComponent();

    expect(screen.getByText('Income & TDS Data Management')).toBeInTheDocument();
    expect(screen.getByText('+ Add Source')).toBeInTheDocument();
    expect(screen.getByText('+ Log Income Entry')).toBeInTheDocument();

    // Check summary card gross income value
    expect(screen.getAllByText('₹1,50,000.00')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Primary Tech Salary')[0]).toBeInTheDocument();
    expect(screen.getByText('May Salary')).toBeInTheDocument();
  });

  test('opens add source modal on button click', () => {
    renderComponent();

    fireEvent.click(screen.getByText('+ Add Source'));
    expect(screen.getByText('Add Income Source')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('e.g. Primary Tech Salary, Freelance Work')).toBeInTheDocument();
  });

  test('opens log income entry modal on button click', () => {
    renderComponent();

    fireEvent.click(screen.getByText('+ Log Income Entry'));
    expect(screen.getByText('Log Income Entry')).toBeInTheDocument();
    expect(screen.getByText('Gross Amount (₹) *')).toBeInTheDocument();
  });
});
