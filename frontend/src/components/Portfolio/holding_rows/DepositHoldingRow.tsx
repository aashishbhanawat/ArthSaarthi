import React from 'react';
import { Holding } from '../../../types/holding';
import { formatInterestRate, usePrivacySensitiveCurrency, formatDate } from '../../../utils/formatting';

interface DepositHoldingRowProps {
    holding: Holding;
    onRowClick: (holding: Holding) => void;
}

const DepositHoldingRow: React.FC<DepositHoldingRowProps> = ({ holding, onRowClick }) => {
    const formatCurrency = usePrivacySensitiveCurrency();

    const assetTypeDisplay = (assetType: string) => {
        if (assetType.toUpperCase() === 'FIXED_DEPOSIT') return 'FD';
        if (assetType.toUpperCase() === 'RECURRING_DEPOSIT') return 'RD';
        return assetType;
    };

    return (
        <tr key={holding.asset_id} className="border-t hover:bg-gray-100 cursor-pointer dark:border-gray-700 dark:hover:bg-gray-700/50" onClick={() => onRowClick(holding)}>
            <td className="p-2 max-w-xs">
                <div className="font-semibold text-gray-900 dark:text-gray-100 break-words">{holding.asset_name}</div>
                <div className="text-sm text-gray-500 dark:text-gray-400">{holding.account_number}</div>
            </td>
            <td className="p-2 text-right font-mono">{assetTypeDisplay(holding.asset_type)}</td>
            <td className="p-2 text-right font-mono">{formatInterestRate(holding.interest_rate)}</td>
            <td className="p-2 text-right font-mono">{holding.maturity_date ? formatDate(holding.maturity_date) : 'N/A'}</td>
            <td className="p-2 text-right font-mono">{formatCurrency(holding.total_invested_amount)}</td>
            <td className="p-2 text-right font-mono">{formatCurrency(holding.current_value)}</td>
        </tr>
    );
};

export default DepositHoldingRow;
