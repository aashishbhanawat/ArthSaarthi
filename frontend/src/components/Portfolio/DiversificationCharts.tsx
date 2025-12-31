import React from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';
import { useDiversification } from '../../hooks/usePortfolios';
import { DiversificationSegment } from '../../types/analytics';

ChartJS.register(ArcElement, Tooltip, Legend);

// Generate distinct colors using HSL color space
const generateColors = (numColors: number) => {
    if (numColors === 0) return [];
    const colors = [];
    for (let i = 0; i < numColors; i++) {
        const hue = (i * (360 / (numColors * 1.618))) % 360;
        colors.push(`hsla(${hue}, 70%, 60%, 0.8)`);
    }
    return colors;
};

interface DiversificationPieChartProps {
    title: string;
    data: DiversificationSegment[];
}

const DiversificationPieChart: React.FC<DiversificationPieChartProps> = ({ title, data }) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const options: any = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'right' as const,
                labels: {
                    boxWidth: 12,
                    font: { size: 11 },
                },
            },
            tooltip: {
                callbacks: {
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    label: (context: any) => {
                        const segment = data[context.dataIndex];
                        return `${context.label}: ₹${segment?.value?.toLocaleString('en-IN') || 0} (${segment?.percentage?.toFixed(1) || 0}%)`;
                    },
                },
            },
        },
    };

    const chartData = {
        labels: data.map((item) => item.name),
        datasets: [
            {
                label: 'Value',
                data: data.map((item) => item.value),
                backgroundColor: generateColors(data.length),
                borderColor: 'rgba(255, 255, 255, 0.8)',
                borderWidth: 1,
            },
        ],
    };

    if (data.length === 0) {
        return (
            <div className="card">
                <h3 className="text-lg font-semibold mb-3">{title}</h3>
                <div className="h-48 flex items-center justify-center text-gray-500">
                    No data available
                </div>
            </div>
        );
    }

    return (
        <div className="card">
            <h3 className="text-lg font-semibold mb-3">{title}</h3>
            <div className="h-48">
                <Pie options={options} data={chartData} />
            </div>
        </div>
    );
};

interface DiversificationChartsProps {
    portfolioId: string;
}

const DiversificationCharts: React.FC<DiversificationChartsProps> = ({ portfolioId }) => {
    const { data, isLoading, isError, error } = useDiversification(portfolioId);

    if (isLoading) {
        return (
            <div className="card">
                <h2 className="text-xl font-semibold mb-4">Diversification Analysis</h2>
                <p className="text-gray-500">Loading diversification data...</p>
            </div>
        );
    }

    if (isError) {
        return (
            <div className="card">
                <h2 className="text-xl font-semibold mb-4">Diversification Analysis</h2>
                <p className="text-red-500">Error: {error.message}</p>
            </div>
        );
    }

    if (!data || data.total_value === 0) {
        return (
            <div className="card">
                <h2 className="text-xl font-semibold mb-4">Diversification Analysis</h2>
                <p className="text-gray-500">
                    No holdings with diversification data. Run "Sync Assets" to enrich your portfolio.
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <h2 className="text-xl font-semibold">Diversification Analysis</h2>

            {/* Row 1: Overview charts */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <DiversificationPieChart
                    title="By Asset Class"
                    data={data.by_asset_class}
                />
                <DiversificationPieChart
                    title="By Geography"
                    data={data.by_country}
                />
                <DiversificationPieChart
                    title="By Market Cap"
                    data={data.by_market_cap}
                />
            </div>

            {/* Row 2: Equity drill-down charts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <DiversificationPieChart
                    title="By Sector (Equities)"
                    data={data.by_sector}
                />
                <DiversificationPieChart
                    title="By Industry (Equities)"
                    data={data.by_industry}
                />
            </div>
        </div>
    );
};

export default DiversificationCharts;
