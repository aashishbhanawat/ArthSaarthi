import { render, screen } from '@testing-library/react';
import AnalyticsCard from '../../../components/Portfolio/AnalyticsCard';
import { PortfolioAnalytics } from '../../../types/analytics';

describe('AnalyticsCard', () => {
    it('should render loading state correctly', () => {
        render(<AnalyticsCard analytics={undefined} isLoading={true} error={null} />);
        expect(screen.getByText('Loading analytics...')).toBeInTheDocument();
    });

    it('should render error state correctly', () => {
        const error = new Error('Failed to fetch analytics');
        render(<AnalyticsCard analytics={undefined} isLoading={false} error={error} />);
        expect(screen.getByText('Error: Failed to fetch analytics')).toBeInTheDocument();
    });

    it('should render no data state correctly', () => {
        render(<AnalyticsCard analytics={undefined} isLoading={false} error={null} />);
        expect(screen.getByText('No analytics data available.')).toBeInTheDocument();
    });

    it('should render success state and format numbers correctly', () => {
        const mockAnalytics: PortfolioAnalytics = {
            xirr: 0.12345,
            sharpe_ratio: 1.23456,
        };
        render(<AnalyticsCard analytics={mockAnalytics} isLoading={false} error={null} />);

        // XIRR should be formatted as a percentage with 2 decimal places
        expect(screen.getByText('12.35%')).toBeInTheDocument(); // 12.345 becomes 12.35
        expect(screen.getByText('XIRR')).toBeInTheDocument();
        // Sharpe Ratio should be formatted as a number with 2 decimal places
        expect(screen.getByText('1.23')).toBeInTheDocument();
        expect(screen.getByText('Sharpe Ratio')).toBeInTheDocument();
    });
});
