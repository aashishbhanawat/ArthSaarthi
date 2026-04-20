import React from 'react';
import { Holding } from '../../../types/holding';
import { usePrivacySensitiveCurrency, formatPercentage, formatDate } from '../../../utils/formatting';

interface BondHoldingRowProps {
    holding: Holding;
    onRowClick: (holding: Holding) => void;
}

const BondHoldingRow: React.FC<BondHoldingRowProps> = ({ holding, onRowClick }) => {
    const formatCurrency = usePrivacySensitiveCurrency();
    return (
        <tr key={holding.asset_id} className="border-t hover:bg-gray-100 cursor-pointer dark:border-gray-700 dark:hover:bg-gray-700/50" onClick={() => onRowClick(holding)}>
            <td className="p-2 max-w-xs">
                <div className="font-semibold text-gray-900 dark:text-gray-100 break-words">{holding.asset_name}</div>
                <div className="text-sm text-gray-500 dark:text-gray-400">{holding.isin}</div>
            </td>
            <td className="p-2 text-right font-mono">{`${Number(holding.interest_rate || 0).toFixed(2)}%`}</td>
            <td className="p-2 text-right font-mono">{holding.maturity_date ? formatDate(holding.maturity_date) : 'N/A'}</td>
            <td className="p-2 text-right font-mono">{formatCurrency(holding.total_invested_amount)}</td>
            <td className="p-2 text-right font-mono">{formatCurrency(holding.current_value)}</td>
            <td className={`p-2 text-right font-mono ${holding.unrealized_pnl >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                <div>{formatCurrency(holding.unrealized_pnl)}</div>
                <div className="text-xs">
                    ({formatPercentage(holding.unrealized_pnl_percentage)})
                </div>
            </td>
        </tr>
    );
};

export default BondHoldingRow;

