import React from 'react';
import { AssetAliasWithAsset } from '../../services/adminApi';
import { PencilIcon, TrashIcon } from '@heroicons/react/24/outline';

interface AliasCardProps {
    alias: AssetAliasWithAsset;
    onEdit: (alias: AssetAliasWithAsset) => void;
    onDelete: (alias: AssetAliasWithAsset) => void;
}

const AliasCard: React.FC<AliasCardProps> = ({ alias, onEdit, onDelete }) => {
    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 mb-3 transition-all hover:shadow-md">
            <div className="flex justify-between items-start mb-2">
                <div className="flex flex-col max-w-[70%]">
                    <span className="text-[10px] text-gray-500 font-medium uppercase tracking-wider">{alias.source}</span>
                    <span className="text-sm font-mono font-bold text-blue-600 dark:text-blue-400 mt-0.5 truncate">{alias.alias_symbol}</span>
                </div>
                <div className="flex items-center gap-1">
                    <button onClick={() => onEdit(alias)} className="p-2 text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors" aria-label="Edit alias">
                        <PencilIcon className="h-4 w-4" />
                    </button>
                    <button onClick={() => onDelete(alias)} className="p-2 text-gray-500 hover:text-red-600 dark:hover:text-red-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors" aria-label="Delete alias">
                        <TrashIcon className="h-4 w-4" />
                    </button>
                </div>
            </div>

            <div className="pt-2 border-t border-gray-50 dark:border-gray-700">
                <div className="flex flex-col">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">Maps To</span>
                    <div className="flex items-baseline gap-2 mt-0.5">
                        <span className="text-sm font-mono font-semibold text-gray-900 dark:text-gray-100">{alias.asset_ticker}</span>
                        <span className="text-xs text-gray-500 dark:text-gray-400 truncate">— {alias.asset_name}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AliasCard;
