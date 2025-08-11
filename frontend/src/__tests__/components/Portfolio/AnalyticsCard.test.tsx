import React from 'react';
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
            realized_xirr: 0.12345,
            unrealized_xirr: -0.05678,
            sharpe_ratio: 1.23456,
        };
        render(<AnalyticsCard analytics={mockAnalytics} isLoading={false} error={null} />);

        // Check for Realized XIRR (formatted as a percentage)
        expect(screen.getByText('Realized XIRR')).toBeInTheDocument();
        expect(screen.getByText('12.35%')).toBeInTheDocument();

        // Check for Unrealized XIRR (formatted as a percentage)
        expect(screen.getByText('Unrealized XIRR')).toBeInTheDocument();
        expect(screen.getByText('-5.68%')).toBeInTheDocument();

        // Check for Sharpe Ratio (formatted as a number)
        expect(screen.getByText('Sharpe Ratio')).toBeInTheDocument();
        expect(screen.getByText('1.23')).toBeInTheDocument();
    });
});
