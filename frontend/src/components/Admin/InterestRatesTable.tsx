import React from 'react';
import { HistoricalInterestRate } from '../../types/asset';
import { formatDate } from '../../utils/formatting';
import { PencilSquareIcon, TrashIcon } from '@heroicons/react/24/outline';

interface InterestRatesTableProps {
    rates: HistoricalInterestRate[];
    onEdit: (rate: HistoricalInterestRate) => void;
    onDelete: (rateId: string) => void;
}

const InterestRatesTable: React.FC<InterestRatesTableProps> = ({ rates, onEdit, onDelete }) => {
    return (
        <div className="overflow-x-auto bg-white rounded-lg shadow">
            <table className="min-w-full">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Scheme Name</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Date</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">End Date</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rate (%)</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {rates.map((rate) => (
                        <tr key={rate.id}>
                            <td className="px-6 py-4 whitespace-nowrap">{rate.scheme_name}</td>
                            <td className="px-6 py-4 whitespace-nowrap">{formatDate(rate.start_date)}</td>
                            <td className="px-6 py-4 whitespace-nowrap">{formatDate(rate.end_date)}</td>
                            <td className="px-6 py-4 whitespace-nowrap">{Number(rate.rate).toFixed(2)}%</td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                <button onClick={() => onEdit(rate)} className="text-indigo-600 hover:text-indigo-900 mr-4">
                                    <PencilSquareIcon className="h-5 w-5" />
                                </button>
                                <button onClick={() => onDelete(rate.id)} className="text-red-600 hover:text-red-900">
                                    <TrashIcon className="h-5 w-5" />
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default InterestRatesTable;
