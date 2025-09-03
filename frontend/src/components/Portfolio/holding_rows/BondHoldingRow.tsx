import React from 'react';
import { Holding } from '../../../types/holding';
import { formatCurrency, formatDate } from '../../../utils/formatting';

interface BondHoldingRowProps {
    holding: Holding;
    onRowClick: (holding: Holding) => void;
}

const BondHoldingRow: React.FC<BondHoldingRowProps> = ({ holding, onRowClick }) => {
    return (
        <tr key={holding.asset_id} className="border-t hover:bg-gray-100 cursor-pointer" onClick={() => onRowClick(holding)}>
            <td className="p-2">
                <div className="font-bold">{holding.asset_name}</div>
                <div className="text-sm text-gray-500">{holding.isin}</div>
            </td>
            <td className="p-2 text-right font-mono">{Number(holding.coupon_rate)?.toFixed(2)}%</td>
            <td className="p-2 text-right font-mono">{holding.maturity_date ? formatDate(holding.maturity_date) : 'N/A'}</td>
            <td className="p-2 text-right font-mono">{formatCurrency(holding.current_value)}</td>
            <td className="p-2"></td>
            <td className="p-2"></td>
            <td className="p-2"></td>
        </tr>
    );
};

export default BondHoldingRow;
