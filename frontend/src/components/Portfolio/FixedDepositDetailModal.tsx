import React from 'react';
import { Holding } from '../../types/holding';
import { formatDate, formatInterestRate, usePrivacySensitiveCurrency } from '../../utils/formatting';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../../services/api';
import { FixedDepositDetails, FixedDepositAnalytics } from '../../types/portfolio';
import { XMarkIcon } from '@heroicons/react/24/solid';

interface FixedDepositDetailModalProps {
    holding: Holding;
    onClose: () => void;
    onEdit: (details: FixedDepositDetails) => void;
    onDelete: () => void;
}

const fetchFdDetails = async (fdId: string): Promise<FixedDepositDetails> => {
    const response = await apiClient.get(`/api/v1/fixed-deposits/${fdId}`);
    return response.data;
};

const fetchFdAnalytics = async (fdId: string): Promise<FixedDepositAnalytics> => {
    const response = await apiClient.get(`/api/v1/fixed-deposits/${fdId}/analytics`);
    return response.data;
};

const FixedDepositDetailModal: React.FC<FixedDepositDetailModalProps> = ({ holding, onClose, onEdit, onDelete }) => {
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
            <div className="modal-content w-full max-w-3xl p-6 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl" onClick={(e) => e.stopPropagation()}>
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-2xl font-bold dark:text-gray-100">Holding Detail: {holding.asset_name}</h2>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-800 hover:bg-gray-100 dark:hover:text-gray-200 dark:hover:bg-gray-700 rounded-full w-8 h-8 flex items-center justify-center transition-colors -mr-2 -mt-2">
                        <XMarkIcon className="h-6 w-6" />
                    </button>
                </div>

                <div className="card mb-4" data-testid="fd-details-section">
                    <h3 className="text-lg font-semibold mb-2 dark:text-gray-100">Details</h3>
                    {isLoadingDetails ? <p className="dark:text-gray-300">Loading...</p> : details && (
                        <div className="grid grid-cols-2 gap-2 text-sm dark:text-gray-300">
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
                    <h3 className="text-lg font-semibold mb-2 dark:text-gray-100">Valuation</h3>
                    {isLoadingDetails ? <p className="dark:text-gray-300">Loading...</p> : details && (
                        <div className="grid grid-cols-2 gap-2 text-sm dark:text-gray-300">
                            <p><strong>Current Value:</strong></p><p>{formatCurrency(holding.current_value)}</p>
                            <p><strong>Unrealized Gain:</strong></p><p>{formatCurrency(holding.unrealized_pnl)}</p>
                            {holding.realized_pnl && holding.realized_pnl > 0 && (
                                <>
                                    <p><strong>Realized Gain:</strong></p><p>{formatCurrency(holding.realized_pnl)}</p>
                                </>
                            )}
                            <p><strong>Maturity Value:</strong></p><p>{formatCurrency(details.maturity_value)} (Projected)</p>
                        </div>
                    )}
                </div>

                <div className="card mb-4">
                    <h3 className="text-lg font-semibold mb-2 dark:text-gray-100">Analytics (XIRR)</h3>
                    {isLoadingAnalytics ? <p className="dark:text-gray-300">Loading...</p> : analytics && (
                        <div className="grid grid-cols-2 gap-2 text-sm dark:text-gray-300">
                            {analytics.realized_xirr > 0 ? (
                                <><p><strong>Final Realized XIRR:</strong></p><p>{formatInterestRate(analytics.realized_xirr * 100)}</p></>
                            ) : (
                                <><p><strong>Annualized Return (XIRR):</strong></p><p>{formatInterestRate(analytics.unrealized_xirr * 100)}</p></>
                            )}
                        </div>
                    )}
                </div>

                <div className="flex justify-end space-x-2">
                    <button className="btn btn-secondary" onClick={() => details && onEdit(details)} disabled={!details}>Edit FD Details</button>
                    <button className="btn btn-danger" onClick={onDelete}>Delete FD</button>
                </div>
            </div>
        </div>
    );
};

export default FixedDepositDetailModal;
