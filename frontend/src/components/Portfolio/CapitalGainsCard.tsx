import React from 'react';
import { CapitalGainsResponse, GainsBreakdown } from '../../types/analytics';
import { usePrivacySensitiveCurrency } from '../../utils/formatting';

interface CapitalGainsCardProps {
    data: CapitalGainsResponse | undefined;
    isLoading: boolean;
    error: Error | null;
}

const GainsRow: React.FC<{ label: string; breakdown: GainsBreakdown }> = ({ label, breakdown }) => {
    const formatCurrency = usePrivacySensitiveCurrency();

    const getColor = (value: number) => {
        if (value > 0) return 'text-green-600 dark:text-green-400';
        if (value < 0) return 'text-red-600 dark:text-red-400';
        return 'text-gray-600 dark:text-gray-400';
    };

    return (
        <tr className="border-b dark:border-gray-700">
            <td className="py-2 px-3 font-medium text-gray-700 dark:text-gray-300">{label}</td>
            <td className={`py-2 px-3 text-right ${getColor(breakdown.gains)}`}>
                {formatCurrency(breakdown.gains)}
            </td>
            <td className={`py-2 px-3 text-right ${getColor(breakdown.losses)}`}>
                {formatCurrency(breakdown.losses)}
            </td>
            <td className={`py-2 px-3 text-right font-semibold ${getColor(breakdown.net)}`}>
                {formatCurrency(breakdown.net)}
            </td>
        </tr>
    );
};

const CapitalGainsCard: React.FC<CapitalGainsCardProps> = ({ data, isLoading, error }) => {
    const formatCurrency = usePrivacySensitiveCurrency();

    if (isLoading) {
        return (
            <div className="card animate-pulse">
                <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4"></div>
                <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="card text-red-500">
                Error loading capital gains: {error.message}
            </div>
        );
    }

    if (!data) {
        return (
            <div className="card text-gray-500 dark:text-gray-400">
                No capital gains data available.
            </div>
        );
    }

    return (
        <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-100">
                Capital Gains Summary
            </h3>

            {/* Unrealized Gains Section */}
            <div className="mb-6">
                <h4 className="text-md font-medium mb-2 text-gray-700 dark:text-gray-300">
                    Unrealized Gains (Current Holdings)
                </h4>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b-2 dark:border-gray-600">
                                <th className="py-2 px-3 text-left text-gray-600 dark:text-gray-400">Term</th>
                                <th className="py-2 px-3 text-right text-gray-600 dark:text-gray-400">Gains</th>
                                <th className="py-2 px-3 text-right text-gray-600 dark:text-gray-400">Losses</th>
                                <th className="py-2 px-3 text-right text-gray-600 dark:text-gray-400">Net</th>
                            </tr>
                        </thead>
                        <tbody>
                            <GainsRow label="Short-term (<1 year)" breakdown={data.unrealized.short_term} />
                            <GainsRow label="Long-term (≥1 year)" breakdown={data.unrealized.long_term} />
                            <tr className="bg-gray-50 dark:bg-gray-800 font-bold">
                                <td className="py-2 px-3 text-gray-800 dark:text-gray-200">Total</td>
                                <td className={`py-2 px-3 text-right ${data.unrealized.total.gains > 0 ? 'text-green-600 dark:text-green-400' : 'text-gray-600'}`}>
                                    {formatCurrency(data.unrealized.total.gains)}
                                </td>
                                <td className={`py-2 px-3 text-right ${data.unrealized.total.losses < 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-600'}`}>
                                    {formatCurrency(data.unrealized.total.losses)}
                                </td>
                                <td className={`py-2 px-3 text-right ${data.unrealized.total.net > 0 ? 'text-green-600 dark:text-green-400' : data.unrealized.total.net < 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-600'}`}>
                                    {formatCurrency(data.unrealized.total.net)}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Holdings Breakdown */}
            {data.holdings_breakdown.length > 0 && (
                <details className="mt-4">
                    <summary className="cursor-pointer text-blue-600 dark:text-blue-400 hover:underline text-sm">
                        View Holdings Detail ({data.holdings_breakdown.length} holdings)
                    </summary>
                    <div className="mt-3 overflow-x-auto">
                        <table className="w-full text-xs">
                            <thead>
                                <tr className="border-b dark:border-gray-600 bg-gray-50 dark:bg-gray-800">
                                    <th className="py-2 px-2 text-left">Asset</th>
                                    <th className="py-2 px-2 text-center">Term</th>
                                    <th className="py-2 px-2 text-right">Days Held</th>
                                    <th className="py-2 px-2 text-right">Cost</th>
                                    <th className="py-2 px-2 text-right">Value</th>
                                    <th className="py-2 px-2 text-right">Gain/Loss</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.holdings_breakdown.map((h) => (
                                    <tr key={h.asset_id} className="border-b dark:border-gray-700">
                                        <td className="py-2 px-2 text-gray-800 dark:text-gray-200">{h.ticker}</td>
                                        <td className="py-2 px-2 text-center">
                                            <span className={`px-2 py-0.5 rounded text-xs ${h.term === 'long_term'
                                                    ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                                                    : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
                                                }`}>
                                                {h.term === 'long_term' ? 'LT' : 'ST'}
                                            </span>
                                        </td>
                                        <td className="py-2 px-2 text-right text-gray-600 dark:text-gray-400">
                                            {h.holding_period_days}
                                        </td>
                                        <td className="py-2 px-2 text-right text-gray-600 dark:text-gray-400">
                                            {formatCurrency(h.cost_basis)}
                                        </td>
                                        <td className="py-2 px-2 text-right text-gray-600 dark:text-gray-400">
                                            {formatCurrency(h.current_value)}
                                        </td>
                                        <td className={`py-2 px-2 text-right font-medium ${h.unrealized_gain > 0 ? 'text-green-600 dark:text-green-400'
                                                : h.unrealized_gain < 0 ? 'text-red-600 dark:text-red-400'
                                                    : 'text-gray-600'
                                            }`}>
                                            {formatCurrency(h.unrealized_gain)}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </details>
            )}
        </div>
    );
};

export default CapitalGainsCard;
