import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { UnrealizedGainsModal } from './UnrealizedGainsModal';
import { PrivacyProvider } from '../../context/PrivacyContext';

const mockSummary = {
    financial_year: '2025-26',
    total_unrealized_stcg: 15000,
    total_unrealized_ltcg: 45000,
    total_unrealized_gain: 60000,
    section_112a_realized_used: 25000,
    section_112a_remaining_headroom: 100000,
    section_112a_unrealized_eligible: 45000,
    section_112a_unrealized_exemption_used: 45000,
    estimated_unrealized_stcg_tax: 3000,
    estimated_unrealized_ltcg_tax: 0,
    total_estimated_tax: 3000,
    lots: [
        {
            holding_id: 'lot-1',
            asset_id: 'asset-1',
            asset_ticker: 'TCS',
            asset_name: 'Tata Consultancy Services',
            asset_type: 'STOCKS',
            buy_date: '2024-01-15',
            quantity: 10,
            buy_price: 3200,
            current_price: 3700,
            total_cost: 32000,
            market_value: 37000,
            unrealized_gain: 5000,
            gain_type: 'LTCG' as const,
            holding_days: 400,
            tax_rate: 'LTCG 12.5% (Sec 112A)',
            estimated_tax: 0,
            is_grandfathered: false,
            is_foreign: false,
            currency: 'INR',
        },
    ],
};

describe('UnrealizedGainsModal', () => {
    it('renders modal when open and displays summary & lots', () => {
        const handleClose = jest.fn();
        render(
            <PrivacyProvider>
                <UnrealizedGainsModal
                    isOpen={true}
                    onClose={handleClose}
                    summary={mockSummary}
                />
            </PrivacyProvider>
        );

        expect(screen.getByText(/Unrealized Capital Gains & Sec 112A Pooling/i)).toBeInTheDocument();
        expect(screen.getByText(/TCS/i)).toBeInTheDocument();
        expect(screen.getByText(/Tata Consultancy Services/i)).toBeInTheDocument();

        // Close button
        const closeBtn = screen.getByRole('button', { name: /close/i });
        fireEvent.click(closeBtn);
        expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it('does not render when isOpen is false', () => {
        render(
            <PrivacyProvider>
                <UnrealizedGainsModal
                    isOpen={false}
                    onClose={jest.fn()}
                    summary={mockSummary}
                />
            </PrivacyProvider>
        );
        expect(screen.queryByText('Unrealized Capital Gains Tax Lots')).not.toBeInTheDocument();
    });
});
