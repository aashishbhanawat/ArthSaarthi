import React from 'react';
import { render, screen } from '@testing-library/react';
import EquityHoldingRow from '../../../../components/Portfolio/holding_rows/EquityHoldingRow';
import { Holding } from '../../../types/holding';

const mockHolding: Holding = {
    asset_id: '1',
    ticker_symbol: 'INFY',
    asset_name: 'Infosys Ltd',
    asset_type: 'STOCK',
    group: 'EQUITIES',
    quantity: 25,
    average_buy_price: 392.81,
    current_price: 1479.10,
    current_value: 36977.50,
    total_invested_amount: 9820.25,
    days_pnl: -490.00,
    unrealized_pnl: 27157.25,
    unrealized_pnl_percentage: 2.7654,
    days_pnl_percentage: 0,
    interest_rate: null,
    maturity_date: null,
    opening_date: null,
    isin: ''
};

describe('EquityHoldingRow', () => {
    it('renders the equity holding data correctly', () => {
        render(
            <table>
                <tbody>
                    <EquityHoldingRow holding={mockHolding} />
                </tbody>
            </table>
        );

        expect(screen.getByText('INFY')).toBeInTheDocument();
        expect(screen.getByText('Infosys Ltd')).toBeInTheDocument();
        expect(screen.getByText('25')).toBeInTheDocument();
        expect(screen.getByText('₹392.81')).toBeInTheDocument();
        expect(screen.getByText('₹1,479.10')).toBeInTheDocument();
        expect(screen.getByText('₹36,977.50')).toBeInTheDocument();
        expect(screen.getByText('-₹490.00')).toBeInTheDocument();
        expect(screen.getByText('₹27,157.25')).toBeInTheDocument();
        expect(screen.getByText('276.54%')).toBeInTheDocument();
    });
});
