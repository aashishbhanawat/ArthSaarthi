import React from 'react';
import { Holding } from '../../types/holding';
import { usePrivacy } from '../../context/PrivacyContext';
import { formatPercentage } from '../../utils/formatting';

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

    const isPositive = Number(holding.unrealized_pnl) >= 0;
    const isDayPositive = Number(holding.days_pnl) >= 0;

    const renderEquitiesInfo = () => (
        <>
            <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                <div>
                    <div className="text-[10px] text-gray-500 uppercase tracking-tighter">Qty</div>
                    <div className="text-xs font-medium dark:text-gray-300">
                        {isPrivacyMode ? '••••' : Number(holding.quantity).toLocaleString()}
                    </div>
                </div>
                <div>
                    <div className="text-[10px] text-gray-500 uppercase tracking-tighter text-center">Avg Price</div>
                    <div className="text-xs font-medium dark:text-gray-300 text-center">
                        {isPrivacyMode ? '••••' : Number(holding.average_buy_price).toFixed(2)}
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-[10px] text-gray-500 uppercase tracking-tighter">LTP</div>
                    <div className="text-xs font-medium dark:text-gray-300">
                        {isPrivacyMode ? '••••' : Number(holding.current_price).toFixed(2)}
                    </div>
                </div>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-2">
                <div className="min-w-0">
                    <div className="text-[10px] text-gray-500 uppercase tracking-tighter truncate">Unrealized P&L</div>
                    <div className={`text-xs font-bold truncate ${isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                        {formatCurrency(holding.unrealized_pnl)} ({formatPercentage(holding.unrealized_pnl_percentage)})
                    </div>
                </div>
                <div className="text-right min-w-0">
                    <div className="text-[10px] text-gray-500 uppercase tracking-tighter truncate">Day's P&L</div>
                    <div className={`text-xs font-bold truncate ${isDayPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                        {formatCurrency(holding.days_pnl)} ({formatPercentage(holding.days_pnl_percentage)})
                    </div>
                </div>
            </div>
        </>
    );

    const renderDepositsInfo = () => (
        <div className="grid grid-cols-2 gap-4 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
            <div>
                <div className="text-[10px] text-gray-500 uppercase tracking-tighter">Interest Rate</div>
                <div className="text-xs font-medium dark:text-gray-300">
                    {holding.interest_rate ? `${holding.interest_rate}%` : 'N/A'}
                </div>
            </div>
            <div className="text-right">
                <div className="text-[10px] text-gray-500 uppercase tracking-tighter">Maturity Date</div>
                <div className="text-xs font-medium dark:text-gray-300">
                    {holding.maturity_date || 'N/A'}
                </div>
            </div>
            <div>
                <div className="text-[10px] text-gray-500 uppercase tracking-tighter">Invested</div>
                <div className="text-xs font-medium dark:text-gray-300">
                    {formatCurrency(holding.total_invested_amount)}
                </div>
            </div>
            <div className="text-right">
                <div className="text-[10px] text-gray-500 uppercase tracking-tighter">Current Value</div>
                <div className="text-xs font-medium dark:text-gray-300">
                    {formatCurrency(holding.current_value)}
                </div>
            </div>
        </div>
    );

    const renderBondsInfo = () => (
        <div className="grid grid-cols-2 gap-4 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
            <div>
                <div className="text-[10px] text-gray-500 uppercase tracking-tighter">Coupon</div>
                <div className="text-xs font-medium dark:text-gray-300">
                    {holding.interest_rate ? `${holding.interest_rate}%` : 'N/A'}
                </div>
            </div>
            <div className="text-right">
                <div className="text-[10px] text-gray-500 uppercase tracking-tighter">Maturity</div>
                <div className="text-xs font-medium dark:text-gray-300">
                    {holding.maturity_date || 'N/A'}
                </div>
            </div>
            <div>
                <div className="text-[10px] text-gray-500 uppercase tracking-tighter">Invested</div>
                <div className="text-xs font-medium dark:text-gray-300">
                    {formatCurrency(holding.total_invested_amount)}
                </div>
            </div>
            <div className="text-right">
                <div className="text-[10px] text-gray-500 uppercase tracking-tighter">Unrealized P&L</div>
                <div className={`text-xs font-bold ${isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    {formatCurrency(holding.unrealized_pnl)}
                </div>
            </div>
        </div>
    );

    const renderSchemesInfo = () => (
        <div className="grid grid-cols-2 gap-4 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
            <div>
                <div className="text-[10px] text-gray-500 uppercase tracking-tighter">Opening Date</div>
                <div className="text-xs font-medium dark:text-gray-300">
                    {holding.opening_date || 'N/A'}
                </div>
            </div>
            <div className="text-right">
                <div className="text-[10px] text-gray-500 uppercase tracking-tighter">Interest Rate</div>
                <div className="text-xs font-medium dark:text-gray-300">
                    {holding.interest_rate ? `${holding.interest_rate}%` : 'N/A'}
                </div>
            </div>
            <div>
                <div className="text-[10px] text-gray-500 uppercase tracking-tighter">Institution</div>
                <div className="text-xs font-medium dark:text-gray-300 truncate">
                    {holding.asset_name}
                </div>
            </div>
            <div className="text-right">
                <div className="text-[10px] text-gray-500 uppercase tracking-tighter">Balance</div>
                <div className="text-xs font-bold dark:text-gray-100">
                    {formatCurrency(holding.current_value)}
                </div>
            </div>
        </div>
    );

    return (
        <div
            onClick={() => onClick(holding)}
            className="card p-4 active:scale-[0.98] transition-all cursor-pointer border-l-4"
            style={{ borderLeftColor: isPositive ? '#10b981' : '#ef4444' }}
        >
            <div className="flex justify-between items-start mb-1 gap-2">
                <div className="flex flex-col min-w-0 flex-1">
                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest truncate">{holding.ticker_symbol}</span>
                    <h3 className="text-sm font-bold text-gray-800 dark:text-gray-100 truncate">{holding.asset_name}</h3>
                </div>
                <div className="text-right flex-shrink-0">
                    <div className="text-sm font-bold text-gray-900 dark:text-gray-100">
                        {formatCurrency(holding.current_value)}
                    </div>
                </div>
            </div>

            {holding.group === 'EQUITIES' && renderEquitiesInfo()}
            {holding.group === 'DEPOSITS' && renderDepositsInfo()}
            {holding.group === 'BONDS' && renderBondsInfo()}
            {holding.group === 'GOVERNMENT_SCHEMES' && renderSchemesInfo()}

            <div className="mt-3 flex gap-2">
                <span className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-[9px] font-bold text-gray-600 dark:text-gray-400">
                    {holding.asset_type}
                </span>
                {holding.investment_style && (
                    <span className="px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/30 rounded text-[9px] font-bold text-blue-600 dark:text-blue-400">
                        {holding.investment_style}
                    </span>
                )}
            </div>
        </div>
    );
};

export default HoldingCard;
