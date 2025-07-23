import React, { useState } from 'react';
import { useDashboardHistory } from '../../hooks/useDashboard';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const PortfolioHistoryChart: React.FC = () => {
  const [range, setRange] = useState('30d');
  const { data, isLoading, isError, error } = useDashboardHistory(range);

  const ranges = [
    { value: '7d', label: '7D' },
    { value: '30d', label: '30D' },
    { value: '1y', label: '1Y' },
    { value: 'all', label: 'All' },
  ];

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: false,
      },
    },
  };

  const chartData = {
    labels: data?.history.map((point) => point.date) || [],
    datasets: [
      {
        label: 'Portfolio Value',
        data: data?.history.map((point) => point.value) || [],
        borderColor: 'rgb(54, 162, 235)',
        backgroundColor: 'rgba(54, 162, 235, 0.5)',
      },
    ],
  };

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Portfolio History</h2>
        <div className="flex items-center space-x-2">
          {ranges.map((r) => (
            <button
              key={r.value}
              onClick={() => setRange(r.value)}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                range === r.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>
      <div className="h-64">
        {isLoading && <p>Loading chart data...</p>}
        {isError && <p className="text-red-500">Error: {error.message}</p>}
        {data && <Line options={options} data={chartData} />}
      </div>
    </div>
  );
};

export default PortfolioHistoryChart;
