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
import type { ChartDataset } from 'chart.js';
import { useBenchmarkComparison } from '../../hooks/usePortfolios';
import { BenchmarkComparisonResponse } from '../../services/portfolioApi';
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
    const [benchmarkTicker, setBenchmarkTicker] = useState<string>("^NSEI");
    const [benchmarkMode, setBenchmarkMode] = useState<string>("single");
    const [hybridPreset, setHybridPreset] = useState<string | null>(null);
    const [showRiskFree, setShowRiskFree] = useState<boolean>(false);
    const [riskFreeRate, setRiskFreeRate] = useState<number>(7.0);
    const [categoryTab, setCategoryTab] = useState<'equity' | 'debt'>('equity');

    const { data, isLoading, error } = useBenchmarkComparison(
        portfolioId,
        benchmarkTicker,
        benchmarkMode,
        hybridPreset,
        riskFreeRate
    );

    const formatPercent = (value: number) => {
        return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
    };

    if (isLoading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg"></div>;
    if (error) return <div className="text-red-500 p-4 bg-red-50 rounded-lg">Failed to load benchmark comparison.</div>;
    if (!data) return null;

    type ChartDataItem = BenchmarkComparisonResponse['chart_data'][number];

    // --- Helper to render a chart from chart_data ---
    const renderChart = (chartDataSrc: ChartDataItem[], benchmarkLabelFull: string) => {
        const datasets: ChartDataset<'line'>[] = [
            {
                label: 'Invested Amount',
                data: chartDataSrc.map(d => d.invested_amount),
                borderColor: 'rgb(156, 163, 175)',
                backgroundColor: 'rgba(156, 163, 175, 0.5)',
                borderDash: [5, 5],
                pointRadius: 0,
                tension: 0.1,
            },
            {
                label: `Hypothetical ${benchmarkLabelFull} Value`,
                data: chartDataSrc.map(d => d.benchmark_value),
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.5)',
                pointRadius: 0,
                tension: 0.1,
            },
        ];

        if (showRiskFree) {
            datasets.push({
                label: `Risk-Free Rate (${riskFreeRate}%) Value`,
                data: chartDataSrc.map(d => d.risk_free_value),
                borderColor: 'rgb(34, 197, 94)',
                backgroundColor: 'rgba(34, 197, 94, 0.5)',
                borderDash: [10, 5],
                pointRadius: 0,
                tension: 0.1,
            });
        }

        const chartDataObj = {
            labels: chartDataSrc.map(d => {
                const date = new Date(d.date);
                return date.toLocaleDateString('en-IN', { month: 'short', year: '2-digit' });
            }),
            datasets,
        };

        const options = {
            responsive: true,
            interaction: {
                mode: 'index' as const,
                intersect: false,
            },
            plugins: {
                legend: { position: 'top' as const },
                tooltip: {
                    callbacks: {
                        label: function (context: TooltipItem<'line'>) {
                            let label = context.dataset.label || '';
                            if (label) label += ': ';
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

        return <Line options={options} data={chartDataObj} />;
    };

    // --- Determine which data source to use based on mode ---
    let currentData: BenchmarkComparisonResponse = data;
    let benchmarkLabel = benchmarkTicker === '^NSEI' ? 'Nifty 50' : 'Sensex';

    if (benchmarkMode === 'hybrid') {
        benchmarkLabel = hybridPreset === 'CRISIL_HYBRID_35_65' ? 'CRISIL Hybrid 35+65' : 'Balanced 50/50';
    }

    if (benchmarkMode === 'category' && data.category_data) {
        if (categoryTab === 'equity' && data.category_data.equity) {
            currentData = data.category_data.equity;
            benchmarkLabel = data.category_data.equity.benchmark_label;
        } else if (categoryTab === 'debt' && data.category_data.debt) {
            currentData = data.category_data.debt;
            benchmarkLabel = data.category_data.debt.benchmark_label;
        } else {
            return <div className="p-4 text-center text-gray-500">No data available for the selected category.</div>;
        }
    }

    const xirrDiff = currentData.portfolio_xirr - currentData.benchmark_xirr;

    const handleSelectionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const val = e.target.value;
        if (val === '^NSEI' || val === '^BSESN') {
            setBenchmarkMode('single');
            setHybridPreset(null);
            setBenchmarkTicker(val);
        } else if (val === 'CRISIL_HYBRID_35_65' || val === 'BALANCED_50_50') {
            setBenchmarkMode('hybrid');
            setHybridPreset(val);
            setBenchmarkTicker('^NSEI');
        } else if (val === 'CATEGORY') {
            setBenchmarkMode('category');
            setHybridPreset(null);
        }
    };

    return (
        <div className="bg-white rounded-lg shadow p-6 mt-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
                <div>
                    <h2 className="text-lg font-semibold text-gray-900">Benchmark Comparison</h2>
                    <p className="text-sm text-gray-500 mt-1">
                        Compare your portfolio's XIRR against a hypothetical investment in the benchmark index.
                    </p>
                </div>
                <div className="mt-4 sm:mt-0 flex flex-col items-end space-y-2">
                    <select
                        value={benchmarkMode === 'hybrid' ? hybridPreset! : benchmarkMode === 'category' ? 'CATEGORY' : benchmarkTicker}
                        onChange={handleSelectionChange}
                        className="block w-64 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                    >
                        <optgroup label="Single Index">
                            <option value="^NSEI">Nifty 50</option>
                            <option value="^BSESN">Sensex</option>
                        </optgroup>
                        <optgroup label="Hybrid Benchmarks">
                            <option value="CRISIL_HYBRID_35_65">CRISIL Hybrid 35+65</option>
                            <option value="BALANCED_50_50">Balanced 50/50</option>
                        </optgroup>
                        <optgroup label="Advanced">
                            <option value="CATEGORY">Category Comparison</option>
                        </optgroup>
                    </select>
                    <div className="flex items-center text-sm">
                        <input
                            type="checkbox"
                            id="riskFreeToggle"
                            checked={showRiskFree}
                            onChange={(e) => setShowRiskFree(e.target.checked)}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <label htmlFor="riskFreeToggle" className="ml-2 text-gray-700">
                            Risk-Free Rate (
                        </label>
                        <input
                            type="number"
                            step="0.1"
                            value={riskFreeRate}
                            onChange={(e) => setRiskFreeRate(parseFloat(e.target.value) || 0)}
                            className="w-12 mx-1 p-0.5 text-center border-b border-gray-300 focus:outline-none focus:border-blue-500 text-sm text-gray-900 dark:text-gray-900 bg-transparent"
                            disabled={!showRiskFree}
                        />
                        <span className="text-gray-700">%)</span>
                    </div>
                </div>
            </div>

            {benchmarkMode === 'category' && (
                <div className="mb-4 border-b border-gray-200">
                    <nav className="-mb-px flex space-x-8" aria-label="Tabs">
                        <button
                            onClick={() => setCategoryTab('equity')}
                            className={`${categoryTab === 'equity'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
                        >
                            Equity
                        </button>
                        <button
                            onClick={() => setCategoryTab('debt')}
                            className={`${categoryTab === 'debt'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
                        >
                            Debt
                        </button>
                    </nav>
                </div>
            )}

            <div className={`grid grid-cols-1 ${showRiskFree ? 'md:grid-cols-4' : 'md:grid-cols-3'} gap-6 mb-8`}>
                <div className="bg-gray-50 rounded-lg p-4 shadow-sm border border-gray-100">
                    <p className="text-sm font-medium text-gray-500 text-center">Portfolio XIRR</p>
                    <div className={`text-3xl font-bold mt-2 text-center ${currentData.portfolio_xirr >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercent(currentData.portfolio_xirr)}
                    </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4 shadow-sm border border-gray-100">
                    <p className="text-sm font-medium text-gray-500 text-center break-words leading-tight">{benchmarkLabel} XIRR</p>
                    <div className={`text-3xl font-bold mt-2 text-center ${currentData.benchmark_xirr >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercent(currentData.benchmark_xirr)}
                    </div>
                </div>
                {showRiskFree && (
                    <div className="bg-green-50 rounded-lg p-4 shadow-sm border border-green-100">
                        <p className="text-sm font-medium text-green-700 text-center">Risk-Free XIRR</p>
                        <div className="text-3xl font-bold mt-2 text-center text-green-700">
                            {formatPercent(data.risk_free_xirr || riskFreeRate)}
                        </div>
                    </div>
                )}
                <div className={`${xirrDiff >= 0 ? 'bg-blue-50 border-blue-100' : 'bg-red-50 border-red-100'} rounded-lg p-4 shadow-sm border`}>
                    <p className="text-sm font-medium text-gray-500 text-center">Alpha vs {benchmarkLabel.split(' ')[0]}</p>
                    <div className={`flex items-center justify-center text-3xl font-bold mt-2 ${xirrDiff >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                        {xirrDiff >= 0 ? <ArrowTrendingUpIcon className="h-8 w-8 mr-1" /> : <ArrowTrendingDownIcon className="h-8 w-8 mr-1" />}
                        {formatPercent(xirrDiff)}
                    </div>
                </div>
            </div>

            <div className="h-96 w-full">
                {renderChart(currentData.chart_data, benchmarkLabel)}
            </div>
        </div>
    );
};

export default BenchmarkComparison;
