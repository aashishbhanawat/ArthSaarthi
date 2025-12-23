import React from 'react';
import { usePrivacySensitiveCurrency } from '../../utils/formatting';

interface SummaryCardProps {
    title: string;
    value: number;
    isPnl?: boolean;
}

const SummaryCard: React.FC<SummaryCardProps> = ({ title, value, isPnl = false }) => {
    const formatCurrency = usePrivacySensitiveCurrency();
    const getPnlColor = (pnlValue: number) => {
        if (pnlValue > 0) return 'text-green-600 dark:text-green-400';
        if (pnlValue < 0) return 'text-red-600 dark:text-red-400';
        return 'text-gray-800 dark:text-gray-200';
    };

    const valueColor = isPnl ? getPnlColor(value) : 'text-gray-800 dark:text-gray-200';

    return (
        <div className="card text-center">
            <h3 className="text-lg font-semibold text-gray-500 dark:text-gray-400 mb-2">{title}</h3>
            <p className={`text-4xl font-bold ${valueColor}`}>{formatCurrency(value)}</p>
        </div>
    );
};

export default SummaryCard;