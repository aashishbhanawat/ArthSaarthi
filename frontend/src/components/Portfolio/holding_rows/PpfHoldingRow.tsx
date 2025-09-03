import React from 'react';
import { Holding } from '../../../types/holding';
import { formatCurrency, formatDate } from '../../../utils/formatting';

interface PpfHoldingRowProps {
    holding: Holding;
    onRowClick: (holding: Holding) => void;
}

const PpfHoldingRow: React.FC<PpfHoldingRowProps> = ({ holding, onRowClick }) => {
    const maturityDate = holding.opening_date ? new Date(holding.opening_date) : null;
    if (maturityDate) {
        maturityDate.setFullYear(maturityDate.getFullYear() + 15);
    }

    return (
        <tr key={holding.asset_id} className="border-t hover:bg-gray-100 cursor-pointer" onClick={() => onRowClick(holding)}>
            <td className="p-2">
                <div className="font-bold">{holding.asset_name}</div>
                <div className="text-sm text-gray-500">{holding.institution_name}</div>
            </td>
            <td className="p-2 text-right font-mono">{holding.institution_name}</td>
            <td className="p-2 text-right font-mono">{maturityDate ? formatDate(maturityDate.toISOString()) : 'N/A'}</td>
            <td className="p-2 text-right font-mono">{formatCurrency(holding.current_value)}</td>
            <td className="p-2"></td>
            <td className="p-2"></td>
            <td className="p-2"></td>
        </tr>
    );
};

export default PpfHoldingRow;
