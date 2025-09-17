import React from 'react';
import { Holding } from '../../../types/holding';
import { formatCurrency, formatDate } from '../../../utils/formatting';

interface SchemeHoldingRowProps {
    holding: Holding;
    onRowClick: (holding: Holding) => void;
}

const SchemeHoldingRow: React.FC<SchemeHoldingRowProps> = ({ holding, onRowClick }) => {
    return (
        <tr
            key={holding.asset_id}
            className="border-t hover:bg-gray-50 cursor-pointer"
            onClick={() => onRowClick(holding)}
            data-testid={`holding-row-${holding.asset_id}`}
        >
            <td className="p-2 font-semibold">PPF Account</td>
            <td className="p-2 text-right">{holding.asset_name}</td>
            <td className="p-2 text-right">{holding.opening_date ? formatDate(holding.opening_date) : 'N/A'}</td>
            <td className="p-2 text-right font-mono">{formatCurrency(holding.current_value)}</td>
        </tr>
    );
};

export default SchemeHoldingRow;