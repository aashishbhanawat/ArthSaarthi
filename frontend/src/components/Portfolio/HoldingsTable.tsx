import React, { useMemo } from 'react';
import * as Accordion from '@radix-ui/react-accordion';
import { ChevronDownIcon } from '@heroicons/react/24/solid';
import groupBy from 'lodash.groupby';
import { Holding } from '../../types/holding';
import { formatCurrency } from '../../utils/formatting';
import EquityHoldingRow from './holding_rows/EquityHoldingRow';
import DepositHoldingRow from './holding_rows/DepositHoldingRow';
import BondHoldingRow from './holding_rows/BondHoldingRow';
// Note: SchemeHoldingRow might not be used in phase 1, but we create it for future use.
// import SchemeHoldingRow from './SchemeHoldingRow';

interface HoldingsTableProps {
    holdings: Holding[] | undefined;
    isLoading: boolean;
    error: Error | null;
    onRowClick: (holding: Holding) => void;
}

const SECTION_CONFIG: { [key: string]: { title: string; columns: { label: string; key: SortKey }[] } } = {
    EQUITIES: {
        title: 'Equities & Mutual Funds',
        columns: [
            { label: 'Asset', key: 'asset_name' },
            { label: 'Qty', key: 'quantity' },
            { label: 'Avg. Price', key: 'average_buy_price' },
            { label: 'LTP', key: 'current_price' },
            { label: 'Value', key: 'current_value' },
            { label: "Day's P&L", key: 'days_pnl' },
            { label: 'Unrealized P&L', key: 'unrealized_pnl' },
            { label: 'Unrealized P&L %', key: 'unrealized_pnl_percentage' },
        ],
    },
    DEPOSITS: {
        title: 'Deposits',
        columns: [
            { label: 'Asset', key: 'asset_name' },
            { label: 'Type', key: 'asset_type' },
            { label: 'Interest Rate', key: 'interest_rate' },
            { label: 'Maturity', key: 'maturity_date' },
            { label: 'Invested', key: 'total_invested_amount' },
            { label: 'Current Value', key: 'current_value' },
        ],
    },
    BONDS: {
        title: 'Bonds & Debentures',
        columns: [
            { label: 'Asset', key: 'asset_name' },
            { label: 'Coupon', key: 'interest_rate' },
            { label: 'Maturity', key: 'maturity_date' },
            { label: 'Invested', key: 'total_invested_amount' },
            { label: 'Mkt. Value', key: 'current_value' },
        ],
    },
    // Add other sections as needed
};

type SortKey = keyof Holding;
type SortDirection = 'ascending' | 'descending';

const HoldingsTable: React.FC<HoldingsTableProps> = ({ holdings, isLoading, error, onRowClick }) => {
    const [sortConfig, setSortConfig] = React.useState<{ [key: string]: { key: SortKey; direction: SortDirection } }>({});

    const groupedAndSortedHoldings = useMemo(() => {
        if (!holdings) return {};
        const grouped = groupBy(holdings, 'group');

        for (const group in grouped) {
            const config = sortConfig[group];
            if (config) {
                grouped[group].sort((a, b) => {
                    const aValue = a[config.key];
                    const bValue = b[config.key];

                    // Handle numeric sorting for string-based numbers from the API
                    const numA = Number(aValue);
                    const numB = Number(bValue);

                    if (!isNaN(numA) && !isNaN(numB)) {
                        return config.direction === 'ascending' ? numA - numB : numB - numA;
                    }

                    // Handle string sorting for non-numeric values
                    if (String(aValue) < String(bValue)) {
                        return config.direction === 'ascending' ? -1 : 1;
                    }
                    if (String(aValue) > String(bValue)) {
                        return config.direction === 'ascending' ? 1 : -1;
                    }
                    return 0;
                });
            }
        }
        return grouped;
    }, [holdings, sortConfig]);

    const requestSort = (group: string, key: SortKey) => {
        let direction: SortDirection = 'ascending';
        if (sortConfig[group] && sortConfig[group].key === key && sortConfig[group].direction === 'ascending') {
            direction = 'descending';
        }
        setSortConfig({ ...sortConfig, [group]: { key, direction } });
    };

    const sectionOrder = ['EQUITIES', 'DEPOSITS', 'BONDS', 'SCHEMES'];

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
            <Accordion.Root type="multiple" defaultValue={sectionOrder} className="space-y-2">
                {sectionOrder.map((group) => {
                    const sectionHoldings = groupedAndSortedHoldings[group];
                    if (!sectionHoldings) return null;

                    const config = SECTION_CONFIG[group];
                    const totalValue = sectionHoldings.reduce((acc, h) => acc + Number(h.current_value), 0);

                    const getSortIndicator = (key: SortKey) => {
                        if (!sortConfig[group] || sortConfig[group].key !== key) return null;
                        return sortConfig[group].direction === 'ascending' ? ' ▲' : ' ▼';
                    };

                    return (
                        <Accordion.Item key={group} value={group} className="border rounded-lg" data-testid={`holdings-section-${group}`}>
                            <Accordion.Header>
                                <Accordion.Trigger className="flex justify-between items-center w-full p-4 font-semibold text-left bg-gray-50 hover:bg-gray-100 rounded-t-lg">
                                    <span>{config.title} (Total Value: {formatCurrency(totalValue)})</span>
                                    <ChevronDownIcon className="w-5 h-5 transition-transform duration-200 ease-in-out transform group-radix-state-open:rotate-180" />
                                </Accordion.Trigger>
                            </Accordion.Header>
                            <Accordion.Content className="overflow-x-auto">
                                <table className="table-auto w-full">
                                    <thead>
                                        <tr className="text-left text-gray-600 text-sm">
                                            {config.columns.map((col, index) => (
                                                <th key={index} className={`p-2 ${index > 0 ? 'text-right' : ''} cursor-pointer`} onClick={() => requestSort(group, col.key)}>
                                                    {col.label}{getSortIndicator(col.key)}
                                                </th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sectionHoldings.map((holding) => {
                                            switch (group) {
                                                case 'EQUITIES':
                                                    return <EquityHoldingRow key={holding.asset_id} holding={holding} onRowClick={onRowClick} />;
                                                case 'DEPOSITS':
                                                    return <DepositHoldingRow key={holding.asset_id} holding={holding} onRowClick={onRowClick} />;
                                                case 'BONDS':
                                                    return <BondHoldingRow key={holding.asset_id} holding={holding} onRowClick={onRowClick} />;
                                                // case 'SCHEMES':
                                                //     return <SchemeHoldingRow key={holding.asset_id} holding={holding} />;
                                                default:
                                                    return null;
                                            }
                                        })}
                                    </tbody>
                                </table>
                            </Accordion.Content>
                        </Accordion.Item>
                    );
                })}
            </Accordion.Root>
        </div>
    );
};

export default HoldingsTable;