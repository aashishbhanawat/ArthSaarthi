import React from 'react';
import { ParsedFixedDeposit } from '../../types/import';

interface ImportFDCardProps {
    fd: ParsedFixedDeposit;
    isSelected: boolean;
    onToggleSelection: () => void;
    isDuplicate: boolean;
    onFieldChange: (field: keyof ParsedFixedDeposit, value: string | number) => void;
}

const ImportFDCard: React.FC<ImportFDCardProps> = ({
    fd,
    isSelected,
    onToggleSelection,
    isDuplicate,
    onFieldChange
}) => {
    return (
        <div
            className={`card p-4 transition-all duration-200 border-l-4 ${isDuplicate ? 'border-l-warning bg-warning/5 dark:bg-warning/10' :
                    'border-l-primary bg-white dark:bg-gray-800'
                } ${!isSelected ? 'opacity-70 grayscale-[0.3]' : 'shadow-md'} mb-4`}
        >
            <div className="flex items-start gap-4 mb-3">
                <div className="pt-1">
                    <input
                        type="checkbox"
                        className="checkbox checkbox-primary checkbox-sm"
                        checked={isSelected}
                        onChange={onToggleSelection}
                    />
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start mb-1">
                        <h3 className="text-base font-bold text-gray-900 dark:text-gray-100 truncate">
                            {fd.bank}
                        </h3>
                        {isDuplicate && (
                            <span className="badge badge-warning badge-xs">Duplicate</span>
                        )}
                    </div>
                    <p className="text-xs text-secondary-500 dark:text-gray-400 font-mono">
                        {fd.account_number}
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="flex flex-col gap-1">
                    <label className="text-[10px] uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400">Principal</label>
                    <input
                        type="number"
                        value={fd.principal_amount}
                        onChange={(e) => onFieldChange('principal_amount', parseFloat(e.target.value))}
                        className="form-input py-1 text-sm bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700 w-full"
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <label className="text-[10px] uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400">Rate (%)</label>
                    <input
                        type="number"
                        step="0.01"
                        value={fd.interest_rate}
                        onChange={(e) => onFieldChange('interest_rate', parseFloat(e.target.value))}
                        className="form-input py-1 text-sm bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700 w-full"
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <label className="text-[10px] uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400">Start Date</label>
                    <input
                        type="date"
                        value={fd.start_date}
                        onChange={(e) => onFieldChange('start_date', e.target.value)}
                        className="form-input py-1 text-sm bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700 w-full"
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <label className="text-[10px] uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400">Maturity Date</label>
                    <input
                        type="date"
                        value={fd.maturity_date}
                        onChange={(e) => onFieldChange('maturity_date', e.target.value)}
                        className="form-input py-1 text-sm bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700 w-full"
                    />
                </div>

                <div className="flex flex-col gap-1 text-left">
                    <label className="text-[10px] uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400">Frequency</label>
                    <select
                        value={fd.compounding_frequency}
                        onChange={(e) => onFieldChange('compounding_frequency', e.target.value)}
                        className="form-select py-1 text-sm bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700 w-full"
                    >
                        <option value="Monthly">Monthly</option>
                        <option value="Quarterly">Quarterly</option>
                        <option value="Half-Yearly">Half-Yearly</option>
                        <option value="Yearly">Yearly</option>
                    </select>
                </div>

                <div className="flex flex-col gap-1">
                    <label className="text-[10px] uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400">Type</label>
                    <select
                        value={fd.interest_payout}
                        onChange={(e) => onFieldChange('interest_payout', e.target.value)}
                        className="form-select py-1 text-sm bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700 w-full"
                    >
                        <option value="Payout">Payout</option>
                        <option value="Cumulative">Cumulative</option>
                    </select>
                </div>
            </div>
        </div>
    );
};

export default ImportFDCard;
