import React from 'react';
import { Holding } from '../../types/holding';
import { usePrivacySensitiveCurrency, formatDate } from '../../utils/formatting';

interface FixedDepositDetailModalProps {
    holding: Holding;
    onClose: () => void;
}

const FixedDepositDetailModal: React.FC<FixedDepositDetailModalProps> = ({ holding, onClose }) => {
    const formatSensitiveCurrency = usePrivacySensitiveCurrency();

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div role="dialog" aria-modal="true" aria-labelledby="fd-detail-modal-title" className="modal-content w-full max-w-lg p-6 border border-gray-200 rounded-lg shadow-xl" onClick={(e) => e.stopPropagation()}>
                <div id="fd-detail-modal-title" className="flex justify-between items-center mb-4">
                    <div>
                        <h2 className="text-2xl font-bold">
                            {holding.asset_name}
                        </h2>
                        <p className="text-sm text-gray-500">{holding.account_number}</p>
                    </div>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-full w-8 h-8 flex items-center justify-center transition-colors -mr-2 -mt-2">
                        <span className="text-2xl leading-none">&times;</span>
                    </button>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-6 bg-gray-50 p-4 rounded-lg">
                    <div>
                        <p className="text-sm text-gray-500">Principal Amount</p>
                        <p className="font-semibold">{formatSensitiveCurrency(holding.total_invested_amount)}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-500">Current Value</p>
                        <p className="font-semibold">{formatSensitiveCurrency(holding.current_value)}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-500">Interest Rate</p>
                        <p className="font-semibold">{holding.interest_rate?.toFixed(2)}%</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-500">Maturity Date</p>
                        <p className="font-semibold">{holding.maturity_date ? formatDate(holding.maturity_date) : 'N/A'}</p>
                    </div>
                </div>

                <div className="flex justify-end mt-6">
                    <button onClick={onClose} className="btn btn-secondary">Close</button>
                </div>
            </div>
        </div>
    );
};

export default FixedDepositDetailModal;
