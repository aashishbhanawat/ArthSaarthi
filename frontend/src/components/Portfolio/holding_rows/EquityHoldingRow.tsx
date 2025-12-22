import React from 'react';
import { Holding } from '../../../types/holding';
import { formatCurrency, usePrivacySensitiveCurrency, formatPercentage } from '../../../utils/formatting';

interface EquityHoldingRowProps {
    holding: Holding;
    onRowClick: (holding: Holding) => void;
}

const PnlCell: React.FC<{ value: number; currency?: string; isPercentage?: boolean }> = ({ value, currency = 'INR', isPercentage = false }) => {
    const formatPrivateCurrency = usePrivacySensitiveCurrency();
    const getPnlColor = (pnl: number) => {
        if (pnl > 0) return 'text-green-600';
        if (pnl < 0) return 'text-red-600';
        return 'text-gray-900';
    };

    const formattedValue = isPercentage ? formatPercentage(value) : formatPrivateCurrency(value, currency);

    return (
        <td className={`p-2 text-right font-mono ${getPnlColor(value)}`}>
            {formattedValue}
        </td>
    );
};

const EquityHoldingRow: React.FC<EquityHoldingRowProps> = ({ holding, onRowClick }) => {
    const formatPrivateCurrency = usePrivacySensitiveCurrency();
    return (
        <tr key={holding.asset_id} className="border-t hover:bg-gray-100 cursor-pointer" onClick={() => onRowClick(holding)}>
            <td className="p-2">
                {holding.asset_type !== 'Mutual Fund' && <div className="font-bold">{holding.ticker_symbol}</div>}
                <div className={`text-sm ${holding.asset_type !== 'Mutual Fund' ? 'text-gray-500' : 'font-semibold text-gray-900'} truncate`}>
                    {holding.asset_name}
                </div>
            </td>
            <td className="p-2 text-right font-mono">{Number(holding.quantity).toLocaleString()}</td>
            <td className="p-2 text-right font-mono">{formatPrivateCurrency(holding.average_buy_price, 'INR')}</td>
            <td className="p-2 text-right font-mono">{formatCurrency(holding.current_price, holding.currency)}</td>
            <td className="p-2 text-right font-mono">{formatPrivateCurrency(holding.current_value, 'INR')}</td>
            <PnlCell value={holding.days_pnl} currency="INR" />
            <PnlCell value={holding.unrealized_pnl} currency="INR" />
            <PnlCell value={holding.unrealized_pnl_percentage} isPercentage />
        </tr>
    );
};

export default EquityHoldingRow;

