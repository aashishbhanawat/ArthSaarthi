import React from 'react';
import { DashboardAsset } from '../../types/dashboard';


interface TopMoversTableProps {
    assets: DashboardAsset[];
}

const TopMoversTable: React.FC<TopMoversTableProps> = ({ assets }) => {
    if (assets.length === 0) {
        return (
            <div className="card">
                <h3 className="text-xl font-semibold mb-4">Top Movers (24h)</h3>
                <div className="flex items-center justify-center h-48 bg-gray-100 rounded-md text-gray-400">
                    <p>No market data available.</p>
                </div>
            </div>
        );
    }

    const formatCurrency = (value: string) => {
        const number = parseFloat(value);
        return `$${number.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    };

    const getPnlColor = (value: string) => {
        const number = parseFloat(value);
        if (number > 0) return 'text-green-600';
        if (number < 0) return 'text-red-600';
        return 'text-gray-800';
    };

    return (
        <div className="card">
            <h3 className="text-xl font-semibold mb-4">Top Movers (24h)</h3>
            <div className="overflow-x-auto">
                <table className="min-w-full bg-white">
                    <thead className="bg-gray-200">
                        <tr>
                            <th className="text-left py-3 px-4 uppercase font-semibold text-sm">Asset</th>
                            <th className="text-right py-3 px-4 uppercase font-semibold text-sm">Price</th>
                            <th className="text-right py-3 px-4 uppercase font-semibold text-sm">Change</th>
                            <th className="text-right py-3 px-4 uppercase font-semibold text-sm">% Change</th>
                        </tr>
                    </thead>
                    <tbody className="text-gray-700">
                        {assets.map((asset) => (
                            <tr key={asset.ticker_symbol} className="border-b odd:bg-gray-50">
                                <td className="text-left py-3 px-4 font-semibold">{asset.ticker_symbol}</td>
                                <td className="text-right py-3 px-4">{formatCurrency(asset.current_price)}</td>
                                <td className={`text-right py-3 px-4 font-bold ${getPnlColor(asset.price_change_24h)}`}>{formatCurrency(asset.price_change_24h)}</td>
                                <td className={`text-right py-3 px-4 font-bold ${getPnlColor(asset.price_change_percentage_24h)}`}>{parseFloat(asset.price_change_percentage_24h).toFixed(2)}%</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default TopMoversTable;