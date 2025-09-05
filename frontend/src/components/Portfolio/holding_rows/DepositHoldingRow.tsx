import React from 'react';
import { Holding } from '../../../types/holding';
import { formatInterestRate, usePrivacySensitiveCurrency, formatDate } from '../../../utils/formatting';

interface DepositHoldingRowProps {
    holding: Holding;
    onRowClick: (holding: Holding) => void;
}

const DepositHoldingRow: React.FC<DepositHoldingRowProps> = ({ holding, onRowClick }) => {
    const formatCurrency = usePrivacySensitiveCurrency();

    return (
        <tr key={holding.asset_id} className="border-t hover:bg-gray-100 cursor-pointer" onClick={() => onRowClick(holding)}>
            <td className="p-2">
                <div className="font-semibold text-gray-900">{holding.asset_name}</div>
                <div className="text-sm text-gray-500">{holding.account_number}</div>
            </td>
            <td className="p-2 text-right font-mono">{formatInterestRate(holding.interest_rate || 0)}</td>
            <td className="p-2 text-right font-mono">{holding.maturity_date ? formatDate(holding.maturity_date) : 'N/A'}</td>
            <td className="p-2 text-right font-mono">{formatCurrency(holding.total_invested_amount)}</td>
            <td className="p-2 text-right font-mono">{formatCurrency(holding.current_value)}</td>
        </tr>
    );
};

export default DepositHoldingRow;
