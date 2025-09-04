import React from 'react';
import { Holding } from '../../types/holding';
import { formatCurrency } from '../../utils/formatting';

interface SchemeHoldingRowProps {
    holding: Holding;
}

const SchemeHoldingRow: React.FC<SchemeHoldingRowProps> = ({ holding }) => {
    return (
        <tr key={holding.asset_id} className="border-t hover:bg-gray-100">
            <td className="p-2">
                <div className="font-semibold text-gray-900">{holding.asset_name}</div>
            </td>
            <td className="p-2 text-right font-mono">{holding.opening_date}</td>
            <td className="p-2 text-right font-mono">{formatCurrency(holding.current_value)}</td>
        </tr>
    );
};

export default SchemeHoldingRow;
