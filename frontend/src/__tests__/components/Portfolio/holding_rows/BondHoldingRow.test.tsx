import React from 'react';
import { render, screen } from '@testing-library/react';
import BondHoldingRow from '../../../../components/Portfolio/holding_rows/BondHoldingRow';
import { formatDate } from '../../../../utils/formatting';
import { Holding } from '../../../types/holding';

const mockHolding: Holding = {
    asset_id: '3',
    asset_name: 'NHAI Bond',
    isin: 'INE906B07CB9',
    asset_type: 'BOND',
    group: 'BONDS',
    quantity: 1,
    average_buy_price: 10100,
    current_price: 10500,
    current_value: 10500,
    total_invested_amount: 10100,
    interest_rate: 8.00,
    maturity_date: '2030-01-01',
    ticker_symbol: '',
    days_pnl: 0,
    days_pnl_percentage: 0,
    unrealized_pnl: 400,
    realized_pnl: 50,
    unrealized_pnl_percentage: 0,
    opening_date: null
};

describe('BondHoldingRow', () => {
    it('renders the bond holding data correctly', () => {
        render(
            <table>
                <tbody>
                    <BondHoldingRow holding={mockHolding} />
                </tbody>
            </table>
        );

        expect(screen.getByText('NHAI Bond')).toBeInTheDocument();
        expect(screen.getByText('INE906B07CB9')).toBeInTheDocument();
        expect(screen.getByText('8.00%')).toBeInTheDocument();
        expect(screen.getByText(formatDate('2030-01-01'))).toBeInTheDocument();
        expect(screen.getByText('₹10,100.00')).toBeInTheDocument();
        expect(screen.getByText('₹10,500.00')).toBeInTheDocument();
    });
});
