import React from 'react';
import { formatCurrency } from '../../utils/formatting';
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/solid';
import { TopMover } from '../../types/dashboard';
import TopMoversCard from './TopMoversCard';

interface TopMoversTableProps {
  assets: TopMover[];
}

const TopMoversTable: React.FC<TopMoversTableProps> = ({ assets }) => {
  if (!assets || assets.length === 0) {
    return (
        <div className="card text-center p-8 text-gray-500">
            No market data available.
        </div>
    );
  }

  return (
    <div className="card">
      <h2 className="text-xl font-bold mb-4">Top Movers (24h)</h2>
        <>
            {/* Desktop Table View */}
            <div className="hidden lg:block overflow-x-auto">
                <table className="table-auto w-full">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                        <tr>
                            <th className="p-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300">Asset</th>
                            <th className="p-3 text-right text-xs font-semibold text-gray-600 dark:text-gray-300">Price</th>
                            <th className="p-3 text-right text-xs font-semibold text-gray-600 dark:text-gray-300">Change</th>
                            <th className="p-3 text-right text-xs font-semibold text-gray-600 dark:text-gray-300">Change %</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                        {assets.map((asset) => {
                            const isPositive = Number(asset.daily_change) >= 0;
                            return (
                                <tr key={asset.ticker_symbol} className="hover:bg-gray-50 dark:hover:bg-gray-750">
                                    <td className="p-3">
                                        <div className="font-medium text-gray-900 dark:text-gray-100">{asset.name}</div>
                                        <div className="text-xs text-gray-500 font-mono">{asset.ticker_symbol}</div>
                                    </td>
                                    <td className="p-3 text-right font-medium">
                                        {formatCurrency(asset.current_price, asset.currency)}
                                    </td>
                                    <td className={`p-3 text-right font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                                        <div className="flex items-center justify-end gap-1">
                                            {isPositive ? <ArrowTrendingUpIcon className="h-4 w-4" /> : <ArrowTrendingDownIcon className="h-4 w-4" />}
                                            {formatCurrency(asset.daily_change, asset.currency)}
                                        </div>
                                    </td>
                                    <td className={`p-3 text-right font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                                        {isPositive ? '+' : ''}{Number(asset.daily_change_percentage).toFixed(2)}%
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {/* Mobile Card View */}
            <div className="lg:hidden space-y-3">
                {assets.map((asset) => (
                    <TopMoversCard key={asset.ticker_symbol} asset={asset} />
                ))}
            </div>
        </>
    </div>
  );
};

export default TopMoversTable;