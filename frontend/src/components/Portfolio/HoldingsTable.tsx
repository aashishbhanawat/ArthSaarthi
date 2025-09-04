import React, { useMemo } from 'react';
import * as Accordion from '@radix-ui/react-accordion';
import { ChevronDownIcon } from '@heroicons/react/24/solid';
import groupBy from 'lodash.groupby';
import { Holding } from '../../types/holding';
import { formatCurrency } from '../../utils/formatting';
import EquityHoldingRow from './EquityHoldingRow';
import DepositHoldingRow from './DepositHoldingRow';
import BondHoldingRow from './BondHoldingRow';
// Note: SchemeHoldingRow might not be used in phase 1, but we create it for future use.
// import SchemeHoldingRow from './SchemeHoldingRow';

interface HoldingsTableProps {
    holdings: Holding[] | undefined;
    isLoading: boolean;
    error: Error | null;
    onRowClick: (holding: Holding) => void;
}

const SECTION_CONFIG: { [key: string]: { title: string; columns: string[] } } = {
    EQUITIES: {
        title: 'Equities & Mutual Funds',
        columns: ['Asset', 'Qty', 'Avg. Price', 'LTP', 'Value', "Day's P&L", 'Unrealized P&L', 'Unrealized P&L %'],
    },
    DEPOSITS: {
        title: 'Deposits',
        columns: ['Asset', 'Interest Rate', 'Maturity', 'Invested', 'Current Value'],
    },
    BONDS: {
        title: 'Bonds & Debentures',
        columns: ['Asset', 'Coupon', 'Maturity', 'Invested', 'Mkt. Value'],
    },
    // Add other sections as needed
};

const HoldingsTable: React.FC<HoldingsTableProps> = ({ holdings, isLoading, error, onRowClick }) => {
    const groupedHoldings = useMemo(() => {
        if (!holdings) return {};
        return groupBy(holdings, 'group');
    }, [holdings]);

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
                    const sectionHoldings = groupedHoldings[group];
                    if (!sectionHoldings) return null;

                    const config = SECTION_CONFIG[group];
                    const totalValue = sectionHoldings.reduce((acc, h) => acc + h.current_value, 0);

                    return (
                        <Accordion.Item key={group} value={group} className="border rounded-lg">
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
                                                <th key={index} className={`p-2 ${index > 0 ? 'text-right' : ''}`}>
                                                    {col}
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