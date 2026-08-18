import React, { useState } from 'react';
import { UnrealizedGainsSummary } from '../../hooks/useCapitalGains';
import { formatCurrency } from '../../utils/formatting';
import { usePrivacy } from '../../context/PrivacyContext';
import { UnrealizedGainsModal } from './UnrealizedGainsModal';

interface UnrealizedGainsCardProps {
    summary: UnrealizedGainsSummary;
}

export const UnrealizedGainsCard: React.FC<UnrealizedGainsCardProps> = ({ summary }) => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const { isPrivacyMode } = usePrivacy();

    const formatVal = (val: number) => {
        if (isPrivacyMode) return '₹ ••••••';
        return formatCurrency(val, 'INR');
    };

    const isTotalGain = summary.total_unrealized_gain >= 0;

    return (
        <>
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5 mb-6 hover:shadow-md transition-shadow">
                <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 mb-4 pb-4 border-b border-gray-100 dark:border-gray-700">
                    <div>
                        <div className="flex items-center gap-2">
                            <h3 className="text-base font-bold text-gray-900 dark:text-gray-100">
                                📊 Unrealized Capital Gains & Exemption Headroom
                            </h3>
                            <span className="bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase">
                                FR6.5 Phase 2
                            </span>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            Estimated gains and statutory Section 112A pooling for active open positions.
                        </p>
                    </div>
                    <button
                        onClick={() => setIsModalOpen(true)}
                        className="self-start sm:self-auto bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-600 text-white font-medium text-xs px-4 py-2 rounded-lg transition-colors shadow-sm flex items-center gap-1.5"
                    >
                        <span>🔍 View Lot Breakdown</span>
                    </button>
                </div>

                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div>
                        <span className="block text-[11px] font-medium text-gray-500 uppercase tracking-tight">
                            Unrealized STCG
                        </span>
                        <span className="text-base font-extrabold text-purple-700 dark:text-purple-400">
                            {formatVal(summary.total_unrealized_stcg)}
                        </span>
                    </div>

                    <div>
                        <span className="block text-[11px] font-medium text-gray-500 uppercase tracking-tight">
                            Unrealized LTCG
                        </span>
                        <span className="text-base font-extrabold text-emerald-700 dark:text-emerald-400">
                            {formatVal(summary.total_unrealized_ltcg)}
                        </span>
                    </div>

                    <div>
                        <span className="block text-[11px] font-medium text-gray-500 uppercase tracking-tight">
                            112A Headroom Left
                        </span>
                        <span className="text-base font-extrabold text-blue-700 dark:text-blue-400">
                            {formatVal(summary.section_112a_remaining_headroom)}
                        </span>
                    </div>

                    <div>
                        <span className="block text-[11px] font-medium text-gray-500 uppercase tracking-tight">
                            Projected Tax
                        </span>
                        <span className="text-base font-extrabold text-amber-700 dark:text-amber-400">
                            {formatVal(summary.total_estimated_tax)}
                        </span>
                    </div>
                </div>
            </div>

            <UnrealizedGainsModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                summary={summary}
            />
        </>
    );
};
