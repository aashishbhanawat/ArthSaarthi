import React from 'react';
import { formatCurrency } from '../../utils/formatting';
import { TopMover } from '../../types/dashboard';


interface TopMoversTableProps {
  assets: TopMover[];
}

const TopMoversTable: React.FC<TopMoversTableProps> = ({ assets }) => {
  const getPnlColor = (value: number) => {
    if (value > 0) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-800';
  };

  return (
    <div className="card">
      <h2 className="text-xl font-bold mb-4">Top Movers (24h)</h2>
      <div className="overflow-x-auto">
        <table className="table-auto w-full">
          <thead>
            <tr className="text-left text-gray-600">
              <th className="p-2">Name</th>
              <th className="p-2 text-right">Price</th>
              <th className="p-2 text-right">Change</th>
            </tr>
          </thead>
          <tbody>
            {assets && assets.length > 0 ? (
              assets.map((asset) => (
                <tr key={asset.ticker_symbol} className="border-t">
                  <td className="p-2">
                    <div className="font-bold">{asset.ticker_symbol}</div>
                    <div className="text-sm text-gray-500">{asset.name}</div>
                  </td>
                  <td className="p-2 text-right font-mono">{formatCurrency(asset.current_price)}</td>
                  <td className={`p-2 text-right font-mono ${getPnlColor(asset.daily_change)}`}>
                    <div>{formatCurrency(asset.daily_change)}</div>
                    <div className="text-sm">({asset.daily_change_percentage.toFixed(2)}%)</div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={3} className="text-center p-4 text-gray-500">
                  No market data available
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TopMoversTable;