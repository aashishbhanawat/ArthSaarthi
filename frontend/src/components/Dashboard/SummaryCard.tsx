import React from 'react';

interface SummaryCardProps {
    title: string;
    value: string;
    valueColorClass?: string;
}

const SummaryCard: React.FC<SummaryCardProps> = ({ title, value, valueColorClass = 'text-gray-800' }) => {
    return (
        <div className="card text-center">
            <h3 className="text-lg font-semibold text-gray-500 mb-2">{title}</h3>
            <p className={`text-4xl font-bold ${valueColorClass}`}>{value}</p>
        </div>
    );
};

export default SummaryCard;