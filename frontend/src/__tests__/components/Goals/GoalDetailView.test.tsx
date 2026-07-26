import { render, screen } from '@testing-library/react';
import React from 'react';
import GoalDetailView from '../../../components/Goals/GoalDetailView';
import { useGoal, useCreateGoalLink, useDeleteGoalLink } from '../../../hooks/useGoals';

// Mock the formatting utility to bypass PrivacyProvider context dependency
jest.mock('../../../utils/formatting', () => ({
  usePrivacySensitiveCurrency: () => (val: number | string) => `₹${val}`,
  formatDate: (d: string) => d,
}));

// Mock search hooks used by AssetLinkModal
jest.mock('../../../hooks/usePortfolios', () => ({
  usePortfolios: () => ({ data: [], isLoading: false }),
}));
jest.mock('../../../hooks/useAssets', () => ({
  useAssetSearch: () => ({ data: [], isLoading: false }),
}));

// Mock the goals hooks
jest.mock('../../../hooks/useGoals');
const mockUseGoal = useGoal as jest.Mock;
const mockUseCreateGoalLink = useCreateGoalLink as jest.Mock;
const mockUseDeleteGoalLink = useDeleteGoalLink as jest.Mock;

// Mock the charting library to inspect props
interface MockLineProps {
  data: {
    labels: string[];
    datasets: Array<{
      data: number[];
      label: string;
    }>;
  };
}
jest.mock('react-chartjs-2', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require('react');
  return {
    Line: (props: MockLineProps) => React.createElement('div', { 'data-testid': 'projection-chart', 'data-props': JSON.stringify(props) }),
  };
});


describe('GoalDetailView', () => {
  const goalId = 'test-goal-id';

  beforeEach(() => {
    mockUseCreateGoalLink.mockReturnValue({ mutate: jest.fn(), isPending: false });
    mockUseDeleteGoalLink.mockReturnValue({ mutate: jest.fn(), isPending: false });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('displays loading state', () => {
    mockUseGoal.mockReturnValue({ isLoading: true });
    render(<GoalDetailView goalId={goalId} />);
    expect(screen.getByText(/loading goal details.../i)).toBeInTheDocument();
  });

  it('displays error state', () => {
    mockUseGoal.mockReturnValue({ error: new Error('Failed to fetch details') });
    render(<GoalDetailView goalId={goalId} />);
    expect(screen.getByText(/failed to fetch details/i)).toBeInTheDocument();
  });

  it('renders all summary values, progress bar, status, and projection chart', () => {
    const mockGoal = {
      id: goalId,
      name: 'Retirement Fund',
      target_amount: 100000.0,
      current_amount: 45000.0,
      target_date: '2028-12-31',
      expected_return: 10.0,
      calculated_return_rate: 12.5,
      required_sip: 550.0,
      progress: 45.0,
      linked_assets_xirr: 14.2,
      projected_future_value: 120000.0,
      status: 'On Track',
      projection_chart_data: [
        { date: '2026-07-25', projected_value: 45000.0, target_value: 45000.0 },
        { date: '2028-12-31', projected_value: 120000.0, target_value: 100000.0 },
      ],
      links: [],
    };

    mockUseGoal.mockReturnValue({ data: mockGoal, isLoading: false });
    render(<GoalDetailView goalId={goalId} />);

    // Check Summary Metrics
    expect(screen.getByText('Target Amount')).toBeInTheDocument();
    expect(screen.getByText('Current Amount')).toBeInTheDocument();
    expect(screen.getByText('Projected Future Value')).toBeInTheDocument();
    expect(screen.getByText('Required Monthly SIP')).toBeInTheDocument();
    expect(screen.getByText('Calculated Return Rate')).toBeInTheDocument();
    expect(screen.getByText('Linked Assets XIRR')).toBeInTheDocument();
    
    // Status Badge
    expect(screen.getByText('On Track')).toBeInTheDocument();
    expect(screen.getByText('On Track')).toHaveClass('text-green-800');

    // Progress
    expect(screen.getByText('45.00%')).toBeInTheDocument();

    // Chart Check
    const chart = screen.getByTestId('projection-chart');
    expect(chart).toBeInTheDocument();

    const props = JSON.parse(chart.getAttribute('data-props') || '{}');
    expect(props.data.labels).toEqual(['2026-07-25', '2028-12-31']);
    expect(props.data.datasets[0].label).toBe('Projected Value (Current holdings)');
    expect(props.data.datasets[0].data).toEqual([45000.0, 120000.0]);
    expect(props.data.datasets[1].label).toBe('Target Path (with required SIP)');
    expect(props.data.datasets[1].data).toEqual([45000.0, 100000.0]);
  });
});
