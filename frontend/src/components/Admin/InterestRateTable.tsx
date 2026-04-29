import React from 'react';
import { HistoricalInterestRate } from '../../types/interestRate';
import { formatDate } from '../../utils/formatting';
import { PencilSquareIcon, TrashIcon } from '@heroicons/react/24/outline';

interface InterestRateTableProps {
  rates: HistoricalInterestRate[];
  onEdit: (rate: HistoricalInterestRate) => void;
  onDelete: (rate: HistoricalInterestRate) => void;
}

const InterestRateTable: React.FC<InterestRateTableProps> = ({ rates, onEdit, onDelete }) => {
  return (
    <div className="overflow-x-auto">
      <table className="table-auto w-full">
        <thead className="bg-gray-100">
          <tr>
            <th className="p-3 text-left">Scheme</th>
            <th className="p-3 text-left">Start Date</th>
            <th className="p-3 text-left">End Date</th>
            <th className="p-3 text-right">Rate (%)</th>
            <th className="p-3 text-center">Actions</th>
          </tr>
        </thead>
        <tbody>
          {rates.map((rate) => (
            <tr key={rate.id} className="border-b hover:bg-gray-50">
              <td className="p-3 font-semibold">{rate.scheme_name}</td>
              <td className="p-3">{formatDate(rate.start_date)}</td>
              <td className="p-3">{rate.end_date ? formatDate(rate.end_date) : 'Current'}</td>
              <td className="p-3 text-right font-mono">{Number(rate.rate).toFixed(2)}%</td>
              <td className="p-3">
                <div className="flex justify-center items-center space-x-4">
                  <button onClick={() => onEdit(rate)} className="text-gray-500 hover:text-blue-600" aria-label={`Edit rate for ${rate.scheme_name}`}>
                    <PencilSquareIcon className="h-5 w-5" />
                  </button>
                  <button onClick={() => onDelete(rate)} className="text-gray-500 hover:text-red-600" aria-label={`Delete rate for ${rate.scheme_name}`}>
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default InterestRateTable;