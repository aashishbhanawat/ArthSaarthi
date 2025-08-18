import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import PortfolioSummary from '../../../components/Portfolio/PortfolioSummary';
import { PortfolioSummary as PortfolioSummaryType } from '../../../types/holding';

describe('PortfolioSummary', () => {
    const mockSummary: PortfolioSummaryType = {
        total_value: 150000.75,
        total_invested_amount: 120000.50,
        days_pnl: 1500.25,
        total_unrealized_pnl: 30000.25,
        total_realized_pnl: -5000.10,
    };

    it('renders loading state correctly', () => {
        render(<PortfolioSummary summary={undefined} isLoading={true} error={null} />);
        const pulseDivs = screen.getAllByText('', { selector: '.animate-pulse div' });
        expect(pulseDivs.length).toBeGreaterThan(0);
    });

    it('renders null when there is an error', () => {
        const { container } = render(<PortfolioSummary summary={undefined} isLoading={false} error={new Error('Failed to fetch')} />);
        expect(container).toBeEmptyDOMElement();
    });

    it('renders null when there is no summary data', () => {
        const { container } = render(<PortfolioSummary summary={undefined} isLoading={false} error={null} />);
        expect(container).toBeEmptyDOMElement();
    });

    it('renders summary data with correct formatting', () => {
        render(<PortfolioSummary summary={mockSummary} isLoading={false} error={null} />);

        expect(screen.getByText('Total Value')).toBeInTheDocument();
        expect(screen.getByText('₹1,50,000.75')).toBeInTheDocument();

        expect(screen.getByText("Day's P&L")).toBeInTheDocument();
        expect(screen.getByText('₹1,500.25')).toBeInTheDocument();

        expect(screen.getByText('Unrealized P&L')).toBeInTheDocument();
        expect(screen.getByText('₹30,000.25')).toBeInTheDocument();

        expect(screen.getByText('Realized P&L')).toBeInTheDocument();
        expect(screen.getByText('-₹5,000.10')).toBeInTheDocument();

        expect(screen.getByText('Total Invested')).toBeInTheDocument();
        expect(screen.getByText('₹1,20,000.50')).toBeInTheDocument();
    });

    it('applies correct colors for P&L values', () => {
        render(<PortfolioSummary summary={mockSummary} isLoading={false} error={null} />);

        // Positive P&L should be green
        const daysPnl = screen.getByText('₹1,500.25');
        expect(daysPnl).toHaveClass('text-green-600');

        // Negative P&L should be red
        const realizedPnl = screen.getByText('-₹5,000.10');
        expect(realizedPnl).toHaveClass('text-red-600');
    });
});