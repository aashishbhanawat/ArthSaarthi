import { render, screen, fireEvent } from '@testing-library/react';
import PortfolioHistoryChart from '../../../components/Dashboard/PortfolioHistoryChart';
import { useDashboardHistory } from '../../../hooks/useDashboard';

// Mock the hook
jest.mock('../../../hooks/useDashboard');
const mockUseDashboardHistory = useDashboardHistory as jest.Mock;

// Mock the charting library to verify props without rendering a canvas
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
    Line: (props: MockLineProps) => React.createElement('div', { 'data-testid': 'line-chart', 'data-props': JSON.stringify(props) }),
  };
});

describe('PortfolioHistoryChart', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('displays a loading message', () => {
    mockUseDashboardHistory.mockReturnValue({ isLoading: true });
    render(<PortfolioHistoryChart />);
    expect(screen.getByText(/loading chart data.../i)).toBeInTheDocument();
  });

  it('displays an error message', () => {
    mockUseDashboardHistory.mockReturnValue({ isError: true, error: { message: 'Failed to fetch' } });
    render(<PortfolioHistoryChart />);
    expect(screen.getByText(/error: failed to fetch/i)).toBeInTheDocument();
  });

  it('renders the line chart with correct data on success', () => {
    const mockData = {
      history: [
        { date: '2023-01-01', value: 100 },
        { date: '2023-01-02', value: 150 },
      ],
    };
    mockUseDashboardHistory.mockReturnValue({ data: mockData, isLoading: false, isError: false });
    render(<PortfolioHistoryChart />);

    const chart = screen.getByTestId('line-chart');
    expect(chart).toBeInTheDocument();

    const props = JSON.parse(chart.getAttribute('data-props') || '{}');
    expect(props.data.labels).toEqual(['2023-01-01', '2023-01-02']);
    expect(props.data.datasets[0].data).toEqual([100, 150]);
    expect(props.data.datasets[0].label).toBe('Portfolio Value');
  });

  it('calls the hook with a new range when a button is clicked', () => {
    mockUseDashboardHistory.mockReturnValue({ data: null, isLoading: false, isError: false });
    render(<PortfolioHistoryChart />);

    expect(mockUseDashboardHistory).toHaveBeenCalledWith('30d');

    const button7d = screen.getByRole('button', { name: /7d/i });
    fireEvent.click(button7d);

    expect(mockUseDashboardHistory).toHaveBeenLastCalledWith('7d');
  });
});