import React from 'react';
import { UnrealizedGainsSummary, UnrealizedTaxLot } from '../../hooks/useCapitalGains';
import { formatCurrency } from '../../utils/formatting';
import { usePrivacy } from '../../context/PrivacyContext';

interface UnrealizedGainsModalProps {
    isOpen: boolean;
    onClose: () => void;
    summary: UnrealizedGainsSummary;
}

export const UnrealizedGainsModal: React.FC<UnrealizedGainsModalProps> = ({
    isOpen,
    onClose,
    summary,
}) => {
    const { isPrivacyMode } = usePrivacy();

    if (!isOpen) return null;

    const parseNum = (val: any) => {
        if (typeof val === 'number') return val;
        if (typeof val === 'string') return parseFloat(val) || 0;
        return 0;
    };

    const formatVal = (val: any, currency: string = 'INR') => {
        if (isPrivacyMode) return '₹ ••••••';
        return formatCurrency(parseNum(val), currency);
    };

    const realizedUsed = parseNum(summary.section_112a_realized_used);
    const unrealizedUsed = parseNum(summary.section_112a_unrealized_exemption_used);
    const remainingHeadroom = parseNum(summary.section_112a_remaining_headroom);

    const headroomPercentage = Math.min(
        100,
        Math.max(
            0,
            ((realizedUsed + unrealizedUsed) / 125000) * 100
        )
    );

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl max-w-5xl w-full max-h-[90vh] flex flex-col overflow-hidden border border-gray-100 dark:border-gray-700">
                {/* Modal Header */}
                <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center bg-gray-50/50 dark:bg-gray-800/50">
                    <div>
                        <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                            <span>📈 Unrealized Capital Gains & Sec 112A Pooling</span>
                            <span className="text-xs font-normal text-gray-500 font-mono">
                                ({summary.financial_year})
                            </span>
                        </h2>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            Lot-level open positions and statutory tax estimates if sold today.
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                        ✕
                    </button>
                </div>

                <div className="p-6 overflow-y-auto space-y-6">
                    {/* Summary Cards Row */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div className="p-4 rounded-xl bg-purple-50/50 dark:bg-purple-900/10 border border-purple-100 dark:border-purple-800/30">
                            <span className="text-xs font-semibold text-purple-600 dark:text-purple-400 uppercase tracking-wide">
                                Unrealized STCG
                            </span>
                            <p className="text-xl font-bold text-purple-900 dark:text-purple-100 mt-1">
                                {formatVal(summary.total_unrealized_stcg)}
                            </p>
                            <span className="text-[10px] text-purple-500 dark:text-purple-400">
                                Est Tax: {formatVal(summary.estimated_unrealized_stcg_tax)}
                            </span>
                        </div>

                        <div className="p-4 rounded-xl bg-emerald-50/50 dark:bg-emerald-900/10 border border-emerald-100 dark:border-emerald-800/30">
                            <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wide">
                                Unrealized LTCG
                            </span>
                            <p className="text-xl font-bold text-emerald-900 dark:text-emerald-100 mt-1">
                                {formatVal(summary.total_unrealized_ltcg)}
                            </p>
                            <span className="text-[10px] text-emerald-500 dark:text-emerald-400">
                                Est Tax: {formatVal(summary.estimated_unrealized_ltcg_tax)}
                            </span>
                        </div>

                        <div className="p-4 rounded-xl bg-blue-50/50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-800/30">
                            <span className="text-xs font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wide">
                                112A Headroom Left
                            </span>
                            <p className="text-xl font-bold text-blue-900 dark:text-blue-100 mt-1">
                                {formatVal(remainingHeadroom)}
                            </p>
                            <span className="text-[10px] text-blue-500 dark:text-blue-400">
                                Total Cap: ₹1,25,000 / FY
                            </span>
                        </div>

                        <div className="p-4 rounded-xl bg-amber-50/50 dark:bg-amber-900/10 border border-amber-100 dark:border-amber-800/30">
                            <span className="text-xs font-semibold text-amber-600 dark:text-amber-400 uppercase tracking-wide">
                                Total Est. Tax
                            </span>
                            <p className="text-xl font-bold text-amber-900 dark:text-amber-100 mt-1">
                                {formatVal(summary.total_estimated_tax)}
                            </p>
                            <span className="text-[10px] text-amber-500 dark:text-amber-400">
                                Projected Liability
                            </span>
                        </div>
                    </div>

                    {/* Section 112A Exemption Progress Bar */}
                    <div className="bg-gray-50 dark:bg-gray-700/30 rounded-xl p-4 border border-gray-100 dark:border-gray-700">
                        <div className="flex justify-between items-center mb-2">
                            <span className="text-xs font-bold text-gray-700 dark:text-gray-300">
                                Section 112A LTCG Exemption Utilization (₹1,25,000 Cap)
                            </span>
                            <span className="text-xs font-mono font-semibold text-gray-600 dark:text-gray-400">
                                {headroomPercentage.toFixed(1)}% Used
                            </span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-600 h-2.5 rounded-full overflow-hidden flex">
                            <div
                                style={{
                                    width: `${Math.min(100, (realizedUsed / 125000) * 100)}%`,
                                }}
                                className="bg-emerald-500 h-full"
                                title="Realized LTCG 112A Exemption"
                            />
                            <div
                                style={{
                                    width: `${Math.min(
                                        100 - (realizedUsed / 125000) * 100,
                                        (unrealizedUsed / 125000) * 100
                                    )}%`,
                                }}
                                className="bg-blue-400 h-full"
                                title="Potential Unrealized 112A Exemption Usage"
                            />
                        </div>
                        <div className="flex justify-between text-[10px] text-gray-500 dark:text-gray-400 mt-2">
                            <span>Realized Used: {formatVal(realizedUsed)}</span>
                            <span>Unrealized Usable: {formatVal(unrealizedUsed)}</span>
                            <span>Remaining Headroom: {formatVal(remainingHeadroom)}</span>
                        </div>
                    </div>


                    {/* Tax Lots Breakdown Table */}
                    <div>
                        <h3 className="text-sm font-bold text-gray-800 dark:text-gray-200 mb-3">
                            Open Tax Lots ({summary.lots.length})
                        </h3>

                        {summary.lots.length === 0 ? (
                            <div className="text-center py-8 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-dashed border-gray-200 dark:border-gray-700">
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                    No open positions with unrealized gains found.
                                </p>
                            </div>
                        ) : (
                            <div className="overflow-x-auto border border-gray-100 dark:border-gray-700 rounded-xl">
                                <table className="w-full text-left border-collapse text-xs">
                                    <thead>
                                        <tr className="bg-gray-50 dark:bg-gray-700/50 text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold border-b border-gray-100 dark:border-gray-700">
                                            <th className="p-3">Asset</th>
                                            <th className="p-3">Buy Date</th>
                                            <th className="p-3 text-right">Holding Days</th>
                                            <th className="p-3 text-right">Qty</th>
                                            <th className="p-3 text-right">Buy Price</th>
                                            <th className="p-3 text-right">Current Price</th>
                                            <th className="p-3 text-right">Unrealized Gain</th>
                                            <th className="p-3 text-center">Tax Category</th>
                                            <th className="p-3 text-right">Est. Tax</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                                        {summary.lots.map((lot: UnrealizedTaxLot, idx: number) => {
                                            const isGain = lot.unrealized_gain >= 0;
                                            return (
                                                <tr
                                                    key={`${lot.holding_id}-${idx}`}
                                                    className="hover:bg-gray-50/50 dark:hover:bg-gray-700/30 transition-colors"
                                                >
                                                    <td className="p-3 font-medium text-gray-900 dark:text-gray-100">
                                                        <div>
                                                            <span>{lot.asset_name || lot.asset_ticker}</span>
                                                            <span className="block text-[10px] text-gray-400 font-mono">
                                                                {lot.asset_ticker} ({lot.asset_type})
                                                            </span>
                                                        </div>
                                                    </td>
                                                    <td className="p-3 font-mono text-gray-600 dark:text-gray-300">
                                                        {new Date(lot.buy_date).toLocaleDateString('en-IN')}
                                                    </td>
                                                    <td className="p-3 text-right font-mono text-gray-600 dark:text-gray-300">
                                                        {lot.holding_days} d
                                                    </td>
                                                    <td className="p-3 text-right font-mono text-gray-600 dark:text-gray-300">
                                                        {Number(lot.quantity).toLocaleString(undefined, {
                                                            maximumFractionDigits: 4,
                                                        })}
                                                    </td>
                                                    <td className="p-3 text-right font-mono text-gray-600 dark:text-gray-300">
                                                        {formatVal(lot.buy_price, lot.currency)}
                                                    </td>
                                                    <td className="p-3 text-right font-mono text-gray-600 dark:text-gray-300">
                                                        {formatVal(lot.current_price, lot.currency)}
                                                    </td>
                                                    <td
                                                        className={`p-3 text-right font-mono font-bold ${
                                                            isGain
                                                                ? 'text-emerald-600 dark:text-emerald-400'
                                                                : 'text-red-600 dark:text-red-400'
                                                        }`}
                                                    >
                                                        {formatVal(lot.unrealized_gain, lot.currency)}
                                                    </td>
                                                    <td className="p-3 text-center">
                                                        <span
                                                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                                                lot.gain_type === 'LTCG'
                                                                    ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300'
                                                                    : 'bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                                                            }`}
                                                        >
                                                            {lot.tax_rate}
                                                        </span>
                                                    </td>
                                                    <td className="p-3 text-right font-mono font-semibold text-gray-800 dark:text-gray-200">
                                                        {lot.gain_type === 'LTCG' && lot.tax_rate?.includes('112A') && isGain ? (
                                                            <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-sans" title="Pooled under Section 112A global ₹1,25,000 exemption cap">
                                                                Pooled (112A)
                                                            </span>
                                                        ) : (
                                                            formatVal(lot.estimated_tax, lot.currency)
                                                        )}
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
