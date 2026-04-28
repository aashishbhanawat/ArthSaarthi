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
        <div className="modal-overlay pt-safe pb-safe p-4" onClick={onClose}>
            <div className="modal-content w-full max-w-3xl max-h-[90vh] flex flex-col border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl" onClick={(e) => e.stopPropagation()}>
                <div className="p-6 pb-2 flex-shrink-0">
                    <div className="flex justify-between items-start mb-4 gap-4">
                        <h2 className="text-xl sm:text-2xl font-bold dark:text-gray-100 break-words min-w-0">
                            Holding Detail: {holding.asset_name}
                        </h2>
                        <button aria-label="Close" onClick={onClose} className="text-gray-500 hover:text-gray-800 hover:bg-gray-100 dark:hover:text-gray-200 dark:hover:bg-gray-700 rounded-full w-8 h-8 flex-shrink-0 flex items-center justify-center transition-colors -mt-1 -mr-1">
                            <XMarkIcon className="h-6 w-6" />
                        </button>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto px-6 py-2 min-h-0">
                    <div className="card mb-4" data-testid="fd-details-section">
                        <h3 className="text-lg font-semibold mb-2 dark:text-gray-100">Details</h3>
                        {isLoadingDetails ? <p className="dark:text-gray-300">Loading...</p> : details && (
                            <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm dark:text-gray-300">
                                <p className="font-semibold">Institution:</p><p className="break-words">{details.name}</p>
                                <p className="font-semibold">Principal Amount:</p><p>{formatCurrency(details.principal_amount)}</p>
                                <p className="font-semibold">Interest Rate:</p><p>{formatInterestRate(details.interest_rate)} p.a.</p>
                                <p className="font-semibold">Start Date:</p><p>{formatDate(details.start_date)}</p>
                                <p className="font-semibold">Maturity Date:</p><p>{formatDate(details.maturity_date)}</p>
                                <p className="font-semibold">Compounding:</p><p>{details.compounding_frequency}</p>
                                <p className="font-semibold">Payout Type:</p><p>{details.interest_payout}</p>
                            </div>
                        )}
                    </div>

                    <div className="card mb-4">
                        <h3 className="text-lg font-semibold mb-2 dark:text-gray-100">Valuation</h3>
                        {isLoadingDetails ? <p className="dark:text-gray-300">Loading...</p> : details && (
                            <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm dark:text-gray-300">
                                <p className="font-semibold">Current Value:</p><p>{formatCurrency(holding.current_value)}</p>
                                <p className="font-semibold">Unrealized Gain:</p><p>{formatCurrency(holding.unrealized_pnl)}</p>
                                {Number(holding.realized_pnl) > 0 && (
                                    <>
                                        <p className="font-semibold">Realized Gain:</p><p>{formatCurrency(holding.realized_pnl || 0)}</p>
                                    </>
                                )}
                                <p className="font-semibold">Maturity Value:</p><p>{formatCurrency(details.maturity_value)} (Projected)</p>
                            </div>
                        )}
                    </div>

                    <div className="card mb-4">
                        <h3 className="text-lg font-semibold mb-2 dark:text-gray-100">Analytics (XIRR)</h3>
                        {isLoadingAnalytics ? <p className="dark:text-gray-300">Loading...</p> : analytics && (
                            <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm dark:text-gray-300">
                                {analytics.realized_xirr > 0 ? (
                                    <><p className="font-semibold">Final Realized XIRR:</p><p>{formatInterestRate(analytics.realized_xirr * 100)}</p></>
                                ) : (
                                    <><p className="font-semibold">Annualized Return (XIRR):</p><p>{formatInterestRate(analytics.unrealized_xirr * 100)}</p></>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                <div className="p-6 pt-4 flex-shrink-0 flex justify-end space-x-2 border-t border-gray-100 dark:border-gray-700">
                    <button className="btn btn-secondary" onClick={() => details && onEdit(details)} disabled={!details}>Edit FD Details</button>
                    <button className="btn btn-danger" onClick={onDelete}>Delete FD</button>
                    <button className="btn btn-secondary md:hidden" onClick={onClose}>Close</button>
                </div>
            </div>
        </div>
    );
};

export default FixedDepositDetailModal;
