import React from 'react';
import { render, screen } from '@testing-library/react';
import DepositHoldingRow from '../../../../components/Portfolio/holding_rows/DepositHoldingRow';
import { Holding } from '../../../../types/holding';
import { PrivacyProvider } from '../../../../context/PrivacyContext';

const mockHolding: Holding = {
    asset_id: 'fd-1',
    asset_name: 'HDFC Bank FD',
    asset_type: 'FIXED_DEPOSIT',
    group: 'DEPOSITS',
    quantity: 1,
    average_buy_price: 100000,
    current_price: 104557.77,
    current_value: 104557.77,
    total_invested_amount: 100000,
    interest_rate: 7.50,
    maturity_date: '2026-03-12',
    account_number: '1234567890',
    ticker_symbol: 'HDFCFD',
    days_pnl: 0,
    days_pnl_percentage: 0,
    unrealized_pnl: 4557.77,
    unrealized_pnl_percentage: 4.56,
    opening_date: null,
    isin: null
};

const renderWithProvider = (component: React.ReactElement) => {
    return render(
        <PrivacyProvider>
            <table>
                <tbody>
                    {component}
                </tbody>
            </table>
        </PrivacyProvider>
    );
}

describe('DepositHoldingRow', () => {
    it('renders the deposit holding data correctly', () => {
        renderWithProvider(<DepositHoldingRow holding={mockHolding} onRowClick={() => {}} />);

        expect(screen.getByText('HDFC Bank FD')).toBeInTheDocument();
        expect(screen.getByText('1234567890')).toBeInTheDocument();
        expect(screen.getByText('FD')).toBeInTheDocument();
        expect(screen.getByText('7.50%')).toBeInTheDocument();
        expect(screen.getByText('12 Mar 2026')).toBeInTheDocument();
        expect(screen.getByText('₹1,00,000.00')).toBeInTheDocument();
        expect(screen.getByText('₹1,04,557.77')).toBeInTheDocument();
    });
});
