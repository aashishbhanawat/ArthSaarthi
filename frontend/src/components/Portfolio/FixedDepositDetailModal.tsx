import React from 'react';
import { Holding } from '../../types/holding';
import { formatDate, formatInterestRate, usePrivacySensitiveCurrency } from '../../utils/formatting';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../../services/api';
import { FixedDepositDetails, FixedDepositAnalytics } from '../../types/portfolio';

interface FixedDepositDetailModalProps {
    holding: Holding;
    onClose: () => void;
}

const fetchFdDetails = async (fdId: string): Promise<FixedDepositDetails> => {
    const response = await apiClient.get(`/api/v1/fixed-deposits/${fdId}`);
    return response.data;
};

const fetchFdAnalytics = async (fdId: string): Promise<FixedDepositAnalytics> => {
    const response = await apiClient.get(`/api/v1/fixed-deposits/${fdId}/analytics`);
    return response.data;
};

const FixedDepositDetailModal: React.FC<FixedDepositDetailModalProps> = ({ holding, onClose }) => {
    const formatCurrency = usePrivacySensitiveCurrency();

    const { data: details, isLoading: isLoadingDetails } = useQuery({
        queryKey: ['fixedDepositDetails', holding.asset_id],
        queryFn: () => fetchFdDetails(holding.asset_id),
    });

    const { data: analytics, isLoading: isLoadingAnalytics } = useQuery({
        queryKey: ['fixedDepositAnalytics', holding.asset_id],
        queryFn: () => fetchFdAnalytics(holding.asset_id),
    });

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <h2 className="text-2xl font-bold mb-4">Holding Detail: {holding.asset_name}</h2>

                <div className="card mb-4" data-testid="fd-details-section">
                    <h3 className="text-lg font-semibold mb-2">Details</h3>
                    {isLoadingDetails ? <p>Loading...</p> : details && (
                        <div className="grid grid-cols-2 gap-2 text-sm">
                            <p><strong>Institution:</strong></p><p>{details.name}</p>
                            <p><strong>Principal Amount:</strong></p><p>{formatCurrency(details.principal_amount)}</p>
                            <p><strong>Interest Rate:</strong></p><p>{formatInterestRate(details.interest_rate)} p.a.</p>
                            <p><strong>Start Date:</strong></p><p>{formatDate(details.start_date)}</p>
                            <p><strong>Maturity Date:</strong></p><p>{formatDate(details.maturity_date)}</p>
                            <p><strong>Compounding:</strong></p><p>{details.compounding_frequency}</p>
                            <p><strong>Payout Type:</strong></p><p>{details.interest_payout}</p>
                        </div>
                    )}
                </div>

                <div className="card mb-4">
                    <h3 className="text-lg font-semibold mb-2">Valuation</h3>
                     {isLoadingDetails ? <p>Loading...</p> : details && (
                        <div className="grid grid-cols-2 gap-2 text-sm">
                            <p><strong>Current Value:</strong></p><p>{formatCurrency(holding.current_value)}</p>
                            <p><strong>Unrealized Gain:</strong></p><p>{formatCurrency(holding.unrealized_pnl)}</p>
                            <p><strong>Maturity Value:</strong></p><p>{formatCurrency(details.maturity_value)} (Projected)</p>
                        </div>
                    )}
                </div>

                <div className="card mb-4">
                    <h3 className="text-lg font-semibold mb-2">Analytics (XIRR)</h3>
                    {isLoadingAnalytics ? <p>Loading...</p> : analytics && (
                         <div className="grid grid-cols-2 gap-2 text-sm">
                            <p><strong>Unrealized XIRR:</strong></p><p>{formatInterestRate(analytics.unrealized_xirr * 100)}</p>
                            <p><strong>Realized XIRR:</strong></p><p>{analytics.realized_xirr > 0 ? formatInterestRate(analytics.realized_xirr * 100) : 'N/A'}</p>
                        </div>
                    )}
                </div>

                <div className="flex justify-end space-x-2">
                    <button className="btn btn-secondary" disabled>Edit FD Details</button>
                    <button className="btn btn-danger" disabled>Delete FD</button>
                    <button className="btn btn-primary" onClick={onClose}>Close</button>
                </div>
            </div>
        </div>
    );
};

export default FixedDepositDetailModal;
