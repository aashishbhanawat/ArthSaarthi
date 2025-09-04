import React from 'react';
import { render, screen } from '@testing-library/react';
import DepositHoldingRow from '../../../../components/Portfolio/holding_rows/DepositHoldingRow';
import { Holding } from '../../../types/holding';

const mockHolding: Holding = {
    asset_id: '2',
    asset_name: 'HDFC Bank FD',
    asset_type: 'FIXED_DEPOSIT',
    group: 'DEPOSITS',
    quantity: 1,
    average_buy_price: 100000,
    current_price: 104557.77,
    current_value: 104557.77,
    total_invested_amount: 100000,
    interest_rate: 0.075,
    maturity_date: '2026-03-12',
    ticker_symbol: '',
    days_pnl: 0,
    days_pnl_percentage: 0,
    unrealized_pnl: 0,
    unrealized_pnl_percentage: 0,
    opening_date: null,
    isin: ''
};

describe('DepositHoldingRow', () => {
    it('renders the deposit holding data correctly', () => {
        render(
            <table>
                <tbody>
                    <DepositHoldingRow holding={mockHolding} />
                </tbody>
            </table>
        );

        expect(screen.getByText('HDFC Bank FD')).toBeInTheDocument();
        expect(screen.getByText('FIXED_DEPOSIT')).toBeInTheDocument();
        expect(screen.getByText('7.50%')).toBeInTheDocument();
        expect(screen.getByText('2026-03-12')).toBeInTheDocument();
        expect(screen.getByText('₹1,00,000.00')).toBeInTheDocument();
        expect(screen.getByText('₹1,04,557.77')).toBeInTheDocument();
    });
});
