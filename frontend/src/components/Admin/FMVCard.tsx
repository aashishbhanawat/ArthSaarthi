import React from 'react';
import { FMVAsset } from '../../services/adminApi';

interface FMVCardProps {
    asset: FMVAsset;
    isEditing: boolean;
    editValue: string;
    onEdit: (ticker: string, currentValue: number | null) => void;
    onSave: (ticker: string) => void;
    onCancel: () => void;
    onFetch: (ticker: string) => void;
    onEditValueChange: (value: string) => void;
    isUpdating: boolean;
    isFetching: boolean;
}

const FMVCard: React.FC<FMVCardProps> = ({
    asset,
    isEditing,
    editValue,
    onEdit,
    onSave,
    onCancel,
    onFetch,
    onEditValueChange,
    isUpdating,
    isFetching,
}) => {
    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 mb-3 transition-all hover:shadow-md">
            <div className="flex justify-between items-start mb-3">
                <div className="flex flex-col max-w-[70%]">
                    <span className="text-[10px] text-gray-400 font-mono tracking-wider">{asset.isin || 'NO ISIN'}</span>
                    <span className="text-sm font-bold text-gray-900 dark:text-gray-100 mt-0.5 truncate">{asset.name}</span>
                    <div className="flex items-center gap-2 mt-1">
                        <span className="text-[11px] font-mono text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 px-1.5 rounded">
                            {asset.ticker_symbol}
                        </span>
                        <span className="text-[10px] text-gray-400 uppercase font-medium">{asset.asset_type}</span>
                    </div>
                </div>
                <div className="text-right">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">FMV 2018</span>
                    {isEditing ? (
                        <input
                            type="number"
                            step="0.01"
                            value={editValue}
                            onChange={(e) => onEditValueChange(e.target.value)}
                            className="input w-24 text-right py-1 mt-1 text-sm"
                            autoFocus
                        />
                    ) : (
                        <span className={`text-base font-extrabold ${asset.fmv_2018 ? 'text-green-600 dark:text-green-400' : 'text-gray-400 italic font-normal'}`}>
                            {asset.fmv_2018 ? `₹${asset.fmv_2018.toFixed(2)}` : 'Not set'}
                        </span>
                    )}
                </div>
            </div>

            <div className="pt-3 border-t border-gray-50 dark:border-gray-700 flex justify-end items-center gap-2">
                {isEditing ? (
                    <>
                        <button
                            onClick={() => onSave(asset.ticker_symbol)}
                            disabled={isUpdating}
                            className="btn btn-primary btn-sm px-4"
                        >
                            {isUpdating ? 'Saving...' : 'Save'}
                        </button>
                        <button
                            onClick={onCancel}
                            className="btn btn-secondary btn-sm px-4"
                        >
                            Cancel
                        </button>
                    </>
                ) : (
                    <>
                        {!asset.fmv_2018 && (
                            <button
                                onClick={() => onFetch(asset.ticker_symbol)}
                                disabled={isFetching}
                                className="btn btn-primary btn-sm px-4"
                                title="Fetch from Yahoo Finance"
                            >
                                {isFetching ? 'Fetching...' : 'Fetch'}
                            </button>
                        )}
                        <button
                            onClick={() => onEdit(asset.ticker_symbol, asset.fmv_2018)}
                            className="btn btn-secondary btn-sm px-4"
                        >
                            Edit
                        </button>
                    </>
                )}
            </div>
        </div>
    );
};

export default FMVCard;
