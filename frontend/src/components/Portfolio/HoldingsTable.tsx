import React, { useState, useMemo } from 'react';
import { Holding } from '../../types/holding';
import { formatCurrency, formatPercentage } from '../../utils/formatting';

interface HoldingsTableProps {
    holdings: Holding[] | undefined;
    isLoading: boolean;
    error: Error | null;
    onRowClick: (holding: Holding) => void;
}

type SortKey = keyof Holding;
type SortDirection = 'ascending' | 'descending';

const PnlCell: React.FC<{ value: number; isPercentage?: boolean }> = ({ value, isPercentage = false }) => {
    const getPnlColor = (pnl: number) => {
        if (pnl > 0) return 'text-green-600';
        if (pnl < 0) return 'text-red-600';
        return 'text-gray-900';
    };

    const formattedValue = isPercentage ? formatPercentage(value) : formatCurrency(value);

    return (
        <td className={`p-2 text-right font-mono ${getPnlColor(value)}`}>
            {formattedValue}
        </td>
    );
};

const HoldingsTable: React.FC<HoldingsTableProps> = ({ holdings, isLoading, error, onRowClick }) => {
    const [sortConfig, setSortConfig] = useState<{ key: SortKey; direction: SortDirection } | null>({
        key: 'current_value',
        direction: 'descending',
    });

    const sortedHoldings = useMemo(() => {
        if (!holdings) return [];
        const sortableItems = [...holdings];
        if (sortConfig !== null) {
            sortableItems.sort((a, b) => {
                if (a[sortConfig.key] < b[sortConfig.key]) {
                    return sortConfig.direction === 'ascending' ? -1 : 1;
                }
                if (a[sortConfig.key] > b[sortConfig.key]) {
                    return sortConfig.direction === 'ascending' ? 1 : -1;
                }
                return 0;
            });
        }
        return sortableItems;
    }, [holdings, sortConfig]);

    const requestSort = (key: SortKey) => {
        let direction: SortDirection = 'ascending';
        if (sortConfig && sortConfig.key === key && sortConfig.direction === 'ascending') {
            direction = 'descending';
        }
        setSortConfig({ key, direction });
    };

    const getSortIndicator = (key: SortKey) => {
        if (!sortConfig || sortConfig.key !== key) return null;
        return sortConfig.direction === 'ascending' ? ' ▲' : ' ▼';
    };

    if (isLoading) {
        return (
            <div className="card animate-pulse">
                <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
                <div className="space-y-2">
                    {Array.from({ length: 5 }).map((_, index) => (
                        <div key={index} className="h-12 bg-gray-200 rounded"></div>
                    ))}
                </div>
            </div>
        );
    }

    if (error) {
        return <div className="card text-center p-8 text-red-500">Error loading holdings: {error.message}</div>;
    }

    if (!holdings || holdings.length === 0) {
        return (
            <div className="card text-center p-8">
                <p className="text-gray-500">You have no current holdings in this portfolio.</p>
                <p className="text-sm text-gray-400 mt-2">Add a "BUY" transaction to get started.</p>
            </div>
        );
    }

    return (
        <div className="card">
            <h2 className="text-xl font-bold mb-4">Holdings</h2>
            <div className="overflow-x-auto">
                <table className="table-auto w-full">
                    <thead>
                        <tr className="text-left text-gray-600 text-sm">
                            <th className="p-2 cursor-pointer hover:bg-gray-100 rounded-l-lg" onClick={() => requestSort('ticker_symbol')}>Asset{getSortIndicator('ticker_symbol')}</th>
                            <th className="p-2 text-right cursor-pointer hover:bg-gray-100" onClick={() => requestSort('quantity')}>Quantity{getSortIndicator('quantity')}</th>
                            <th className="p-2 text-right cursor-pointer hover:bg-gray-100" onClick={() => requestSort('average_buy_price')}>Avg. Buy Price{getSortIndicator('average_buy_price')}</th>
                            <th className="p-2 text-right cursor-pointer hover:bg-gray-100" onClick={() => requestSort('current_price')}>Current Price{getSortIndicator('current_price')}</th>
                            <th className="p-2 text-right cursor-pointer hover:bg-gray-100" onClick={() => requestSort('current_value')}>Current Value{getSortIndicator('current_value')}</th>
                            <th className="p-2 text-right cursor-pointer hover:bg-gray-100" onClick={() => requestSort('days_pnl')}>Day's P&L{getSortIndicator('days_pnl')}</th>
                            <th className="p-2 text-right cursor-pointer hover:bg-gray-100" onClick={() => requestSort('unrealized_pnl')}>Unrealized P&L{getSortIndicator('unrealized_pnl')}</th>
                            <th className="p-2 text-right cursor-pointer hover:bg-gray-100 rounded-r-lg" onClick={() => requestSort('unrealized_pnl_percentage')}>Unrealized P&L %{getSortIndicator('unrealized_pnl_percentage')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedHoldings.map((holding) => (
                            <tr key={holding.asset_id} className="border-t hover:bg-gray-100 cursor-pointer" onClick={() => onRowClick(holding)}>
                                <td className="p-2">
                                    {/* For Mutual Funds, the name is sufficient and the ticker (scheme code) is not user-friendly. */}
                                    {holding.asset_type !== 'Mutual Fund' && <div className="font-bold">{holding.ticker_symbol}</div>}
                                    <div className={`text-sm ${holding.asset_type !== 'Mutual Fund' ? 'text-gray-500' : 'font-semibold text-gray-900'} truncate`}>
                                        {holding.asset_name}
                                    </div>
                                </td>
                                <td className="p-2 text-right font-mono">{Number(holding.quantity).toLocaleString()}</td>
                                <td className="p-2 text-right font-mono">{formatCurrency(holding.average_buy_price)}</td>
                                <td className="p-2 text-right font-mono">{formatCurrency(holding.current_price)}</td>
                                <td className="p-2 text-right font-mono">{formatCurrency(holding.current_value)}</td>
                                <PnlCell value={holding.days_pnl} />
                                <PnlCell value={holding.unrealized_pnl} />
                                <PnlCell value={holding.unrealized_pnl_percentage} isPercentage />
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default HoldingsTable;