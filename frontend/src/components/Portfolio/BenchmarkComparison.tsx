import React, { useState } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    TooltipItem
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { useBenchmarkComparison } from '../../hooks/usePortfolios';
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/solid';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

interface Props {
    portfolioId: string;
}

const BenchmarkComparison: React.FC<Props> = ({ portfolioId }) => {
    const [benchmarkTicker, setBenchmarkTicker] = useState<"^NSEI" | "^BSESN">("^NSEI");
    const { data, isLoading, error } = useBenchmarkComparison(portfolioId, benchmarkTicker);

    const formatPercent = (value: number) => {
        return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
    };

    if (isLoading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg"></div>;
    if (error) return <div className="text-red-500 p-4 bg-red-50 rounded-lg">Failed to load benchmark comparison.</div>;
    if (!data) return null;

    const chartData = {
        labels: data.chart_data.map(d => {
            const date = new Date(d.date);
            return date.toLocaleDateString('en-IN', { month: 'short', year: '2-digit' });
        }),
        datasets: [
            {
                label: 'Invested Amount',
                data: data.chart_data.map(d => d.invested_amount),
                borderColor: 'rgb(156, 163, 175)', // Gray-400
                backgroundColor: 'rgba(156, 163, 175, 0.5)',
                borderDash: [5, 5],
                pointRadius: 0,
                tension: 0.1,
            },
            {
                label: `Hypothetical ${benchmarkTicker === '^NSEI' ? 'Nifty 50' : 'Sensex'} Value`,
                data: data.chart_data.map(d => d.benchmark_value),
                borderColor: 'rgb(59, 130, 246)', // Blue-500
                backgroundColor: 'rgba(59, 130, 246, 0.5)',
                pointRadius: 0,
                tension: 0.1,
            },
        ],
    };

    const options = {
        responsive: true,
        interaction: {
            mode: 'index' as const,
            intersect: false,
        },
        plugins: {
            legend: {
                position: 'top' as const,
            },
            tooltip: {
                callbacks: {
                    label: function (context: TooltipItem<'line'>) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        if (context.parsed.y !== null) {
                            label += new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(context.parsed.y);
                        }
                        return label;
                    }
                }
            }
        },
        scales: {
            y: {
                ticks: {
                    callback: function (value: string | number) {
                        const numValue = typeof value === 'string' ? parseFloat(value) : value;
                        if (Math.abs(numValue) >= 10000000) return (numValue / 10000000).toFixed(1) + 'Cr';
                        if (Math.abs(numValue) >= 100000) return (numValue / 100000).toFixed(1) + 'L';
                        if (Math.abs(numValue) >= 1000) return (numValue / 1000).toFixed(1) + 'k';
                        return value;
                    }
                }
            }
        }
    };

    const xirrDiff = data.portfolio_xirr - data.benchmark_xirr;

    return (
        <div className="bg-white rounded-lg shadow p-6 mt-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
                <div>
                    <h2 className="text-lg font-semibold text-gray-900">Benchmark Comparison</h2>
                    <p className="text-sm text-gray-500 mt-1">
                        Compare your portfolio's XIRR against a hypothetical investment in the benchmark index.
                    </p>
                </div>
                <div className="mt-4 sm:mt-0">
                    <select
                        value={benchmarkTicker}
                        onChange={(e) => setBenchmarkTicker(e.target.value as "^NSEI" | "^BSESN")}
                        className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                    >
                        <option value="^NSEI">Nifty 50</option>
                        <option value="^BSESN">Sensex</option>
                    </select>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm font-medium text-gray-500">Your Portfolio XIRR</p>
                    <div className={`text-2xl font-bold mt-1 ${data.portfolio_xirr >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercent(data.portfolio_xirr)}
                    </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm font-medium text-gray-500">Benchmark XIRR ({benchmarkTicker === '^NSEI' ? 'Nifty 50' : 'Sensex'})</p>
                    <div className={`text-2xl font-bold mt-1 ${data.benchmark_xirr >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercent(data.benchmark_xirr)}
                    </div>
                    <p className="text-xs text-gray-400 mt-1">Hypothetical investment matching your cash flows</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm font-medium text-gray-500">Alpha (Excess Return)</p>
                    <div className={`flex items-center text-2xl font-bold mt-1 ${xirrDiff >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {xirrDiff >= 0 ? <ArrowTrendingUpIcon className="h-6 w-6 mr-1" /> : <ArrowTrendingDownIcon className="h-6 w-6 mr-1" />}
                        {formatPercent(xirrDiff)}
                    </div>
                </div>
            </div>

            <div className="h-80 w-full">
                <Line options={options} data={chartData} />
            </div>
        </div>
    );
};

export default BenchmarkComparison;
