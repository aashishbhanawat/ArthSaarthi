import React from 'react';
import { Holding } from '../../types/holding';
import { usePrivacy } from '../../context/PrivacyContext';

interface HoldingCardProps {
    holding: Holding;
    onClick: (holding: Holding) => void;
}

const HoldingCard: React.FC<HoldingCardProps> = ({ holding, onClick }) => {
    const { isPrivacyMode } = usePrivacy();

    const formatCurrency = (value: number) => {
        if (isPrivacyMode) return '₹ ••••••';
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0,
        }).format(value);
    };

    const formatPercent = (value: number) => {
        return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
    };

    const isPositive = holding.unrealized_pnl >= 0;

    return (
        <div 
            onClick={() => onClick(holding)}
            className="card p-4 mb-3 active:scale-[0.98] transition-all cursor-pointer border-l-4"
            style={{ borderLeftColor: isPositive ? '#10b981' : '#ef4444' }}
        >
            <div className="flex justify-between items-start mb-2">
                <div className="flex flex-col max-w-[70%]">
                    <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{holding.ticker_symbol}</span>
                    <h3 className="text-base font-bold text-gray-800 dark:text-gray-100 truncate">{holding.asset_name}</h3>
                </div>
                <div className="text-right">
                    <div className="text-sm font-bold text-gray-900 dark:text-gray-100">
                        {formatCurrency(holding.current_value)}
                    </div>
                    <div className={`text-xs font-semibold ${isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                        {formatPercent(holding.unrealized_pnl_percentage)}
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                <div>
                    <div className="text-[10px] text-gray-500 uppercase tracking-tighter">Avg Buy / Qty</div>
                    <div className="text-xs font-medium dark:text-gray-300">
                        {isPrivacyMode ? '••••' : holding.average_buy_price.toFixed(2)} / {holding.quantity}
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-[10px] text-gray-500 uppercase tracking-tighter">Unrealized P&L</div>
                    <div className={`text-xs font-bold ${isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                        {formatCurrency(holding.unrealized_pnl)}
                    </div>
                </div>
            </div>
            
            <div className="mt-2 flex gap-2">
                 <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-[10px] font-medium text-gray-600 dark:text-gray-400">
                    {holding.asset_type}
                </span>
                {holding.investment_style && (
                     <span className="px-2 py-0.5 bg-blue-50 dark:bg-blue-900/30 rounded text-[10px] font-medium text-blue-600 dark:text-blue-400">
                        {holding.investment_style}
                    </span>
                )}
            </div>
        </div>
    );
};

export default HoldingCard;
