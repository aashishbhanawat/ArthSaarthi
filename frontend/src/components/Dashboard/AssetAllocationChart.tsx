import React from 'react';
import { useDashboardAllocation } from '../../hooks/useDashboard';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { AssetAllocation } from '../../types/dashboard';
import { Pie } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

// Helper to generate dynamic colors for the chart slices
const generateColors = (numColors: number) => {
  if (numColors === 0) return [];
  const colors = [];
  for (let i = 0; i < numColors; i++) {
    // Use HSL color space to generate distinct, pleasant colors
    const hue = (i * (360 / (numColors * 1.618))) % 360; // Use golden angle for distribution
    colors.push(`hsla(${hue}, 70%, 60%, 0.8)`);
  }
  return colors;
};

const AssetAllocationChart: React.FC = () => {
  const { data, isLoading, isError, error } = useDashboardAllocation();

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
    labels: data?.map((item: AssetAllocation) => item.ticker) || [],
    datasets: [
      {
        label: 'Value',
        data: data?.map((item: AssetAllocation) => item.value) || [],
        backgroundColor: generateColors(data?.length || 0),
        borderColor: 'rgba(255, 255, 255, 0.8)',
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-4">Asset Allocation</h2>
      <div className="h-64">
        {isLoading && <p>Loading chart data...</p>}
        {isError && <p className="text-red-500">Error: {error.message}</p>}
        {data && <Pie options={options} data={chartData} />}
      </div>
    </div>
  );
};

export default AssetAllocationChart;
