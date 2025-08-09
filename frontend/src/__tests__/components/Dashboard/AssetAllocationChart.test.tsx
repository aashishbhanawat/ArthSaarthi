import { render, screen } from '@testing-library/react';
import AssetAllocationChart from '../../../components/Dashboard/AssetAllocationChart';
import { useDashboardAllocation } from '../../../hooks/useDashboard';

// Mock the hook
jest.mock('../../../hooks/useDashboard');
const mockUseDashboardAllocation = useDashboardAllocation as jest.Mock;

// Mock the charting library to verify props without rendering a canvas
interface MockPieProps {
  data: {
    labels: string[];
    datasets: Array<{
      data: number[];
      backgroundColor: string[];
    }>;
  };
}

jest.mock('react-chartjs-2', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require('react');
  return {
    Pie: (props: MockPieProps) => React.createElement('div', { 'data-testid': 'pie-chart', 'data-props': JSON.stringify(props) }),
  };
});

describe('AssetAllocationChart', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('displays a loading message', () => {
    mockUseDashboardAllocation.mockReturnValue({ isLoading: true });
    render(<AssetAllocationChart />);
    expect(screen.getByText(/loading chart data.../i)).toBeInTheDocument();
  });

  it('displays an error message', () => {
    mockUseDashboardAllocation.mockReturnValue({ isError: true, error: { message: 'Failed to fetch' } });
    render(<AssetAllocationChart />);
    expect(screen.getByText(/error: failed to fetch/i)).toBeInTheDocument();
  });

  it('renders the pie chart with correct data on success', () => {
    const mockData = {
      allocation: [
        { ticker: 'AAPL', value: 5000 },
        { ticker: 'GOOGL', value: 3000 },
      ],
    };
    mockUseDashboardAllocation.mockReturnValue({ data: mockData, isLoading: false, isError: false });
    render(<AssetAllocationChart />);

    const chart = screen.getByTestId('pie-chart');
    expect(chart).toBeInTheDocument();

    const props = JSON.parse(chart.getAttribute('data-props') || '{}');
    expect(props.data.labels).toEqual(['AAPL', 'GOOGL']);
    expect(props.data.datasets[0].data).toEqual([5000, 3000]);
    expect(props.data.datasets[0].backgroundColor).toHaveLength(2);
  });

  it('renders the pie chart correctly with no data', () => {
    mockUseDashboardAllocation.mockReturnValue({ data: { allocation: [] }, isLoading: false, isError: false });
    render(<AssetAllocationChart />);

    const chart = screen.getByTestId('pie-chart');
    expect(chart).toBeInTheDocument();
  });
});