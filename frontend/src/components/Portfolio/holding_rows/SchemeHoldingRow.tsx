import React from 'react';
import { Holding } from '../../../types/holding';
import { usePrivacySensitiveCurrency, formatDate } from '../../../utils/formatting';

interface SchemeHoldingRowProps {
    holding: Holding;
    onRowClick: (holding: Holding) => void;
}

const SchemeHoldingRow: React.FC<SchemeHoldingRowProps> = ({ holding, onRowClick }) => {
    const formatCurrency = usePrivacySensitiveCurrency();
    return (
        <tr key={holding.asset_id} className="border-t hover:bg-gray-100 cursor-pointer" onClick={() => onRowClick(holding)}>
            <td className="p-2">
                <div className="font-mono text-xs text-gray-500">{holding.asset_type}</div>
            </td>
            <td className="p-2 text-right font-mono">{holding.asset_name}</td>
            <td className="p-2 text-right font-mono">{holding.opening_date ? formatDate(holding.opening_date) : 'N/A'}</td>
            <td className="p-2 text-right font-mono">{formatCurrency(holding.current_value)}</td>
        </tr>
    );
};

export default SchemeHoldingRow;

