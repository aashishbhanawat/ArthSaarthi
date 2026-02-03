import React, { useState, useMemo } from 'react';
import { useCapitalGains, GainEntry, ForeignGainEntry, ITRRow } from '../hooks/useCapitalGains';
import { useScheduleFA, ScheduleFAEntry } from '../hooks/useScheduleFA';
import { formatCurrency } from '../utils/formatting';

// Helper to get current FY
const getCurrentFY = (): string => {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth(); // 0-indexed
    // FY starts in April (month 3)
    if (month >= 3) {
        return `${year}-${(year + 1).toString().slice(-2)}`;
    }
    return `${year - 1}-${year.toString().slice(-2)}`;
};

// FY options for dropdown
const generateFYOptions = (): string[] => {
    const options: string[] = [];
    const currentYear = new Date().getFullYear();
    for (let i = 0; i < 5; i++) {
        const startYear = currentYear - i;
        options.push(`${startYear}-${(startYear + 1).toString().slice(-2)}`);
    }
    return options;
};

// Calendar year options for Schedule FA
const generateCalendarYearOptions = (): number[] => {
    const options: number[] = [];
    const currentYear = new Date().getFullYear();
    for (let i = 0; i < 5; i++) {
        options.push(currentYear - i);
    }
    return options;
};

// Format quantity with 4 decimals
const formatQty = (qty: number | string): string => {
    const num = typeof qty === 'string' ? parseFloat(qty) : qty;
    return num.toLocaleString('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
};

// Format currency with 2 decimals
const formatCurrency2 = (val: number | string, prefix?: string): string => {
    const num = typeof val === 'string' ? parseFloat(val) : val;
    const formatted = num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return prefix ? `${prefix} ${formatted}` : formatted;
};

type TabType = 'capital-gains' | 'schedule-fa';

const CapitalGainsPage: React.FC = () => {
    const [activeTab, setActiveTab] = useState<TabType>('capital-gains');
    const [selectedFY, setSelectedFY] = useState<string>(getCurrentFY());
    const [slabRate, setSlabRate] = useState<number>(30); // Default 30%
    const [selectedCalendarYear, setSelectedCalendarYear] = useState<number>(new Date().getFullYear() - 1);
    const fyOptions = useMemo(() => generateFYOptions(), []);
    const calendarYearOptions = useMemo(() => generateCalendarYearOptions(), []);

    const { data, isLoading, isError, error } = useCapitalGains({ fy: selectedFY, slab_rate: slabRate });
    const { data: faData, isLoading: faLoading, isError: faError, error: faErrorObj } = useScheduleFA({ calendar_year: selectedCalendarYear });

    const periodLabels = ['Upto 15/6', '16/6 - 15/9', '16/9 - 15/12', '16/12 - 15/3', '16/3 - 31/3'];

    return (
        <div className="p-4">
            <h1 className="text-3xl font-bold mb-6 dark:text-white">Tax Reports</h1>

            {/* Tab Navigation */}
            <div className="flex border-b border-gray-200 dark:border-gray-700 mb-6">
                <button
                    onClick={() => setActiveTab('capital-gains')}
                    className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${activeTab === 'capital-gains'
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
                        }`}
                >
                    Capital Gains
                </button>
                <button
                    onClick={() => setActiveTab('schedule-fa')}
                    className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${activeTab === 'schedule-fa'
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
                        }`}
                >
                    Schedule FA (Foreign Assets)
                </button>
            </div>

            {/* Capital Gains Tab */}
            {activeTab === 'capital-gains' && (
                <>
                    {/* FY and Slab Rate Selector */}
                    <div className="mb-6 flex items-center gap-4 flex-wrap">
                        <div className="flex items-center gap-2">
                            <label htmlFor="fy-select" className="font-medium dark:text-gray-200">Financial Year:</label>
                            <select
                                id="fy-select"
                                value={selectedFY}
                                onChange={(e) => setSelectedFY(e.target.value)}
                                className="form-input w-36"
                            >
                                {fyOptions.map((fy) => (
                                    <option key={fy} value={fy}>FY {fy}</option>
                                ))}
                            </select>
                        </div>

                        <div className="flex items-center gap-2">
                            <label htmlFor="slab-rate" className="font-medium dark:text-gray-200">Tax Slab (%):</label>
                            <input
                                id="slab-rate"
                                type="number"
                                value={slabRate}
                                onChange={(e) => setSlabRate(Number(e.target.value))}
                                className="form-input w-20"
                                min="0"
                                max="100"
                            />
                        </div>

                        <div className="flex-grow"></div>

                        <button
                            onClick={() => {
                                window.open(
                                    `/api/v1/capital-gains/export?fy=${selectedFY}&slab_rate=${slabRate}`,
                                    '_blank'
                                );
                            }}
                            className="btn btn-secondary flex items-center gap-2"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                            </svg>
                            Export CSV
                        </button>
                    </div>

                    {isLoading && <div className="text-center p-8 dark:text-gray-300">Loading capital gains data...</div>}
                    {isError && <div className="text-center p-8 text-red-500">Error: {(error as Error).message}</div>}

                    {data && (
                        <>
                            {/* Summary Cards */}
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                                    <h3 className="text-sm text-gray-500 dark:text-gray-400">Total STCG</h3>
                                    <p className={`text-2xl font-bold ${data.total_stcg >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                        {formatCurrency(data.total_stcg, 'INR')}
                                    </p>
                                </div>
                                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                                    <h3 className="text-sm text-gray-500 dark:text-gray-400">Total LTCG</h3>
                                    <p className={`text-2xl font-bold ${data.total_ltcg >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                        {formatCurrency(data.total_ltcg, 'INR')}
                                    </p>
                                </div>
                                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                                    <h3 className="text-sm text-gray-500 dark:text-gray-400">Est. STCG Tax</h3>
                                    <p className="text-2xl font-bold text-orange-600">
                                        {formatCurrency(data.estimated_stcg_tax, 'INR')}
                                    </p>
                                </div>
                                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                                    <h3 className="text-sm text-gray-500 dark:text-gray-400">Est. LTCG Tax</h3>
                                    <p className="text-2xl font-bold text-orange-600">
                                        {formatCurrency(data.estimated_ltcg_tax, 'INR')}
                                    </p>
                                </div>
                            </div>

                            {/* ITR-2 Schedule CG Matrix */}
                            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-8 overflow-x-auto">
                                <h2 className="text-xl font-semibold mb-4 dark:text-white">ITR-2 Schedule CG (Advance Tax Breakdown)</h2>
                                <table className="min-w-full text-sm">
                                    <thead>
                                        <tr className="bg-gray-100 dark:bg-gray-700">
                                            <th className="p-2 text-left dark:text-gray-200">Category</th>
                                            {periodLabels.map((label) => (
                                                <th key={label} className="p-2 text-right dark:text-gray-200">{label}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {(data.itr_schedule_cg || []).map((row: ITRRow, idx: number) => (
                                            <tr key={idx} className="border-b dark:border-gray-600">
                                                <td className="p-2 font-medium dark:text-gray-200">{row.category_label}</td>
                                                <td className="p-2 text-right dark:text-gray-300">{formatCurrency(row.period_values.upto_15_6, 'INR')}</td>
                                                <td className="p-2 text-right dark:text-gray-300">{formatCurrency(row.period_values.upto_15_9, 'INR')}</td>
                                                <td className="p-2 text-right dark:text-gray-300">{formatCurrency(row.period_values.upto_15_12, 'INR')}</td>
                                                <td className="p-2 text-right dark:text-gray-300">{formatCurrency(row.period_values.upto_15_3, 'INR')}</td>
                                                <td className="p-2 text-right dark:text-gray-300">{formatCurrency(row.period_values.upto_31_3, 'INR')}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4 mb-8">
                                <div className="flex gap-2">
                                    <span className="text-xl">⚠️</span>
                                    <div className="text-sm text-yellow-800 dark:text-yellow-200 space-y-1">
                                        <p>
                                            Tax estimates are for informational purposes only. Please consult a tax professional for accurate filing.
                                        </p>
                                        <p>
                                            <strong>Hybrid / Balanced Funds:</strong> Funds marked with ⚠️ may vary in taxation (Equity vs Debt) depending on their equity component (e.g. &gt;65% Equity). Please verify manually.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Detailed Gains Table */}
                            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 overflow-x-auto">
                                <h2 className="text-xl font-semibold mb-4 dark:text-white">Realized Gains ({(data.gains || []).length} transactions)</h2>
                                <table className="min-w-full text-sm">
                                    <thead>
                                        <tr className="bg-gray-100 dark:bg-gray-700">
                                            <th className="p-2 text-left dark:text-gray-200">Asset</th>
                                            <th className="p-2 text-left dark:text-gray-200">Type</th>
                                            <th className="p-2 text-right dark:text-gray-200">Qty</th>
                                            <th className="p-2 text-right dark:text-gray-200">Buy Date</th>
                                            <th className="p-2 text-right dark:text-gray-200">Sell Date</th>
                                            <th className="p-2 text-right dark:text-gray-200">Days</th>
                                            <th className="p-2 text-right dark:text-gray-200">Buy Value</th>
                                            <th className="p-2 text-right dark:text-gray-200">Sell Value</th>
                                            <th className="p-2 text-right dark:text-gray-200">Gain/Loss</th>
                                            <th className="p-2 text-center dark:text-gray-200">Category</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {(data.gains || []).map((gain: GainEntry) => (
                                            <tr key={gain.transaction_id} className="border-b dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700">
                                                <td className="p-2 dark:text-gray-200">
                                                    <div className="flex flex-col">
                                                        <div className="flex items-center gap-1">
                                                            <span className="font-medium">{gain.asset_name || gain.asset_ticker}</span>
                                                            {gain.is_hybrid_warning && (
                                                                <span title="Hybrid Fund: Tax rate depends on equity exposure. Verify manually." className="cursor-help text-yellow-500">
                                                                    ⚠️
                                                                </span>
                                                            )}
                                                        </div>
                                                        <span className="text-xs text-gray-500 dark:text-gray-400">{gain.asset_ticker}</span>
                                                    </div>
                                                    <div className="flex gap-1 mt-1">
                                                        {gain.is_grandfathered && <span className="text-xs bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-200 px-1 rounded">GF</span>}
                                                        {gain.corporate_action_adjusted && <span className="text-xs bg-orange-100 dark:bg-orange-800 text-orange-700 dark:text-orange-200 px-1 rounded">CA</span>}
                                                    </div>
                                                </td>
                                                <td className="p-2 dark:text-gray-300">{gain.asset_type}</td>
                                                <td className="p-2 text-right dark:text-gray-300">{formatQty(gain.quantity)}</td>
                                                <td className="p-2 text-right dark:text-gray-300">{new Date(gain.buy_date).toLocaleDateString('en-IN')}</td>
                                                <td className="p-2 text-right dark:text-gray-300">{new Date(gain.sell_date).toLocaleDateString('en-IN')}</td>
                                                <td className="p-2 text-right dark:text-gray-300">{gain.holding_days}</td>
                                                <td className="p-2 text-right dark:text-gray-300">{formatCurrency(gain.total_buy_value, 'INR')}</td>
                                                <td className="p-2 text-right dark:text-gray-300">{formatCurrency(gain.total_sell_value, 'INR')}</td>
                                                <td className={`p-2 text-right font-medium ${gain.gain >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                    {formatCurrency(gain.gain, 'INR')}
                                                </td>
                                                <td className="p-2 text-center">
                                                    <span className={`px-2 py-1 rounded text-xs font-medium ${gain.gain_type === 'LTCG' ? 'bg-green-100 dark:bg-green-800 text-green-700 dark:text-green-200' : 'bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-200'}`}>
                                                        {gain.tax_rate}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            {/* Schedule 112A Section (if applicable) */}
                            {(data.schedule_112a || []).length > 0 && (
                                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mt-8 overflow-x-auto">
                                    <div className="flex justify-between items-center mb-4">
                                        <h2 className="text-xl font-semibold dark:text-white">Schedule 112A (Grandfathered Equity LTCG)</h2>
                                        <button
                                            onClick={() => {
                                                window.open(
                                                    `/api/v1/capital-gains/export?fy=${selectedFY}&report_type=112a`,
                                                    '_blank'
                                                );
                                            }}
                                            className="px-3 py-1.5 text-sm font-medium border border-gray-300 rounded hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700 dark:text-gray-300 flex items-center gap-2"
                                        >
                                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                                            </svg>
                                            Export CSV
                                        </button>
                                    </div>
                                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                                        Detailed breakdown for ITR-2 Schedule 112A filing.
                                    </p>
                                    <table className="min-w-full text-sm">
                                        <thead>
                                            <tr className="bg-gray-100 dark:bg-gray-700">
                                                <th className="p-2 text-left dark:text-gray-200">ISIN</th>
                                                <th className="p-2 text-left dark:text-gray-200">Name</th>
                                                <th className="p-2 text-right dark:text-gray-200">Qty</th>
                                                <th className="p-2 text-right dark:text-gray-200">Sale Value</th>
                                                <th className="p-2 text-right dark:text-gray-200">Original Cost</th>
                                                <th className="p-2 text-right dark:text-gray-200">FMV 31 Jan 2018</th>
                                                <th className="p-2 text-right dark:text-gray-200">Final Cost</th>
                                                <th className="p-2 text-right dark:text-gray-200">Capital Gain</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {data.schedule_112a.map((entry, idx) => (
                                                <tr key={idx} className="border-b dark:border-gray-600">
                                                    <td className="p-2 font-mono text-xs dark:text-gray-200">{entry.isin}</td>
                                                    <td className="p-2 dark:text-gray-200">{entry.asset_name}</td>
                                                    <td className="p-2 text-right dark:text-gray-300">{formatQty(entry.quantity)}</td>
                                                    <td className="p-2 text-right dark:text-gray-300">{formatCurrency(entry.full_value_consideration, 'INR')}</td>
                                                    <td className="p-2 text-right dark:text-gray-300">{formatCurrency(entry.cost_of_acquisition_orig, 'INR')}</td>
                                                    <td className="p-2 text-right dark:text-gray-300">{entry.fmv_31jan2018 ? formatCurrency(entry.fmv_31jan2018, 'INR') : '-'}</td>
                                                    <td className="p-2 text-right dark:text-gray-300">{formatCurrency(entry.cost_of_acquisition_final, 'INR')}</td>
                                                    <td className={`p-2 text-right font-medium ${entry.balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                        {formatCurrency(entry.balance, 'INR')}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}

                            {/* Foreign Capital Gains Section */}
                            {(data.foreign_gains || []).length > 0 && (
                                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mt-8 overflow-x-auto">
                                    <h2 className="text-xl font-semibold mb-4 dark:text-white">Foreign Capital Gains</h2>
                                    <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-4 mb-4">
                                        <p className="text-sm text-blue-800 dark:text-blue-200">
                                            <strong>📌 Note:</strong> Values shown in native currency. For ITR filing, convert to INR as per IT rules (consult tax consultant).
                                            After conversion, add the capital gain to the respective tax category (STCG/LTCG).
                                        </p>
                                    </div>
                                    <table className="min-w-full text-sm">
                                        <thead>
                                            <tr className="bg-gray-100 dark:bg-gray-700">
                                                <th className="p-2 text-left dark:text-gray-200">Asset</th>
                                                <th className="p-2 text-left dark:text-gray-200">Currency</th>
                                                <th className="p-2 text-right dark:text-gray-200">Qty</th>
                                                <th className="p-2 text-right dark:text-gray-200">Buy Date</th>
                                                <th className="p-2 text-right dark:text-gray-200">Sell Date</th>
                                                <th className="p-2 text-right dark:text-gray-200">Days</th>
                                                <th className="p-2 text-right dark:text-gray-200">Buy Value</th>
                                                <th className="p-2 text-right dark:text-gray-200">Sell Value</th>
                                                <th className="p-2 text-right dark:text-gray-200">Gain/Loss</th>
                                                <th className="p-2 text-center dark:text-gray-200">Type</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {data.foreign_gains.map((gain: ForeignGainEntry) => (
                                                <tr key={gain.transaction_id} className="border-b dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700">
                                                    <td className="p-2 dark:text-gray-200">
                                                        <span className="font-medium">{gain.asset_ticker}</span>
                                                        {gain.country_code && (
                                                            <span className="ml-1 text-xs bg-gray-100 dark:bg-gray-600 text-gray-600 dark:text-gray-300 px-1 rounded">
                                                                {gain.country_code}
                                                            </span>
                                                        )}
                                                    </td>
                                                    <td className="p-2 dark:text-gray-300 font-mono">{gain.currency}</td>
                                                    <td className="p-2 text-right dark:text-gray-300">{formatQty(gain.quantity)}</td>
                                                    <td className="p-2 text-right dark:text-gray-300">{new Date(gain.buy_date).toLocaleDateString('en-IN')}</td>
                                                    <td className="p-2 text-right dark:text-gray-300">{new Date(gain.sell_date).toLocaleDateString('en-IN')}</td>
                                                    <td className="p-2 text-right dark:text-gray-300">{gain.holding_days}</td>
                                                    <td className="p-2 text-right dark:text-gray-300">{formatCurrency2(gain.total_buy_value, gain.currency)}</td>
                                                    <td className="p-2 text-right dark:text-gray-300">{formatCurrency2(gain.total_sell_value, gain.currency)}</td>
                                                    <td className={`p-2 text-right font-medium ${gain.gain >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                        {formatCurrency2(gain.gain, gain.currency)}
                                                    </td>
                                                    <td className="p-2 text-center">
                                                        <span className={`px-2 py-1 rounded text-xs font-medium ${gain.gain_type === 'LTCG' ? 'bg-green-100 dark:bg-green-800 text-green-700 dark:text-green-200' : 'bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-200'}`}>
                                                            {gain.gain_type}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </>
                    )}
                </>
            )}

            {/* Schedule FA Tab */}
            {activeTab === 'schedule-fa' && (
                <>
                    {/* Calendar Year Selector and Export */}
                    <div className="mb-6 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <label htmlFor="cy-select" className="font-medium dark:text-gray-200">Calendar Year:</label>
                            <select
                                id="cy-select"
                                value={selectedCalendarYear}
                                onChange={(e) => setSelectedCalendarYear(parseInt(e.target.value))}
                                className="form-input w-40"
                            >
                                {calendarYearOptions.map((cy) => (
                                    <option key={cy} value={cy}>{cy}</option>
                                ))}
                            </select>
                            <span className="text-sm text-gray-500 dark:text-gray-400">
                                (For AY {selectedCalendarYear + 1}-{(selectedCalendarYear + 2).toString().slice(-2)})
                            </span>
                        </div>
                        <button
                            onClick={() => {
                                // Simple client-side CSV export
                                if (!faData) return;
                                const headers = [
                                    "Country Name", "Country Code", "Entity Name", "Address", "Zip Code",
                                    "Nature", "Date Acquired", "Initial Value", "Peak Value",
                                    "Closing Value", "Gross Amount Received", "Gross Proceeds", "Currency"
                                ];
                                const rows = faData.entries.map(e => [
                                    `"${e.country_name}"`, `"${e.country_code}"`, `"${e.entity_name}"`,
                                    `"${e.entity_address}"`, `"${e.zip_code}"`, `"${e.nature_of_entity}"`,
                                    `"${e.date_acquired}"`, e.initial_value, e.peak_value,
                                    e.closing_value, e.gross_amount_received, e.gross_proceeds_from_sale, e.currency
                                ].join(","));
                                const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows].join("\n");
                                const encodedUri = encodeURI(csvContent);
                                const link = document.createElement("a");
                                link.setAttribute("href", encodedUri);
                                link.setAttribute("download", `schedule_fa_${selectedCalendarYear}.csv`);
                                /* eslint-disable testing-library/no-node-access */
                                document.body.appendChild(link);
                                link.click();
                                document.body.removeChild(link);
                                /* eslint-enable testing-library/no-node-access */
                            }}
                            className="btn btn-secondary flex items-center gap-2"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                            </svg>
                            Export CSV
                        </button>
                    </div>

                    {/* Info Banner */}
                    <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-4 mb-6">
                        <p className="text-sm text-blue-800 dark:text-blue-200">
                            <strong>📌 Schedule FA:</strong> Reports foreign assets held during the calendar year (Jan 1 - Dec 31).
                            Values shown in native currency. For ITR filing, convert to INR as per IT rules (consult tax consultant).
                        </p>
                    </div>

                    {faLoading && <div className="text-center p-8 dark:text-gray-300">Loading foreign assets data...</div>}
                    {faError && <div className="text-center p-8 text-red-500">Error: {(faErrorObj as Error).message}</div>}

                    {faData && (
                        <>
                            {/* Summary Cards */}
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                                    <h3 className="text-sm text-gray-500 dark:text-gray-400">Initial Value (Jan 1)</h3>
                                    <p className="text-xl font-bold dark:text-white">
                                        {faData.entries.length > 0 ? formatCurrency2(faData.total_initial_value, faData.entries[0]?.currency) : '-'}
                                    </p>
                                </div>
                                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                                    <h3 className="text-sm text-gray-500 dark:text-gray-400">Peak Value</h3>
                                    <p className="text-xl font-bold text-green-600">
                                        {faData.entries.length > 0 ? formatCurrency2(faData.total_peak_value, faData.entries[0]?.currency) : '-'}
                                    </p>
                                </div>
                                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                                    <h3 className="text-sm text-gray-500 dark:text-gray-400">Closing Value (Dec 31)</h3>
                                    <p className="text-xl font-bold dark:text-white">
                                        {faData.entries.length > 0 ? formatCurrency2(faData.total_closing_value, faData.entries[0]?.currency) : '-'}
                                    </p>
                                </div>
                                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                                    <h3 className="text-sm text-gray-500 dark:text-gray-400">Gross Proceeds</h3>
                                    <p className="text-xl font-bold text-orange-600">
                                        {faData.entries.length > 0 ? formatCurrency2(faData.total_gross_proceeds, faData.entries[0]?.currency) : '-'}
                                    </p>
                                </div>
                            </div>

                            {/* Schedule FA Table */}
                            {faData.entries.length === 0 ? (
                                <div className="text-center p-8 text-gray-500 dark:text-gray-400">
                                    No foreign assets found for calendar year {selectedCalendarYear}.
                                </div>
                            ) : (
                                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 overflow-x-auto">
                                    <h2 className="text-xl font-semibold mb-4 dark:text-white">
                                        Schedule FA A3 - Foreign Equity & Debt ({faData.entries.length} entries)
                                    </h2>
                                    <table className="min-w-full text-sm">
                                        <thead>
                                            <tr className="bg-gray-100 dark:bg-gray-700">
                                                <th className="p-2 text-left dark:text-gray-200">Country</th>
                                                <th className="p-2 text-left dark:text-gray-200">Name of Entity</th>
                                                <th className="p-2 text-left dark:text-gray-200">Nature</th>
                                                <th className="p-2 text-right dark:text-gray-200">Date Acquired</th>
                                                <th className="p-2 text-right dark:text-gray-200">Initial Value</th>
                                                <th className="p-2 text-right dark:text-gray-200">Peak Value</th>
                                                <th className="p-2 text-right dark:text-gray-200">Closing Balance</th>
                                                <th className="p-2 text-right dark:text-gray-200">Gross Paid/Credited</th>
                                                <th className="p-2 text-right dark:text-gray-200">Gross Proceeds</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {faData.entries.map((entry: ScheduleFAEntry, idx: number) => (
                                                <tr key={idx} className="border-b dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700">
                                                    <td className="p-2 dark:text-gray-200">
                                                        <div className="font-medium">{entry.country_name}</div>
                                                    </td>
                                                    <td className="p-2 dark:text-gray-200">
                                                        <div className="font-medium">{entry.entity_name}</div>
                                                        <div className="text-xs text-gray-500 font-mono">{entry.asset_ticker}</div>
                                                    </td>
                                                    <td className="p-2 dark:text-gray-300">{entry.nature_of_entity}</td>
                                                    <td className="p-2 text-right dark:text-gray-300 font-mono">
                                                        {entry.date_acquired ? new Date(entry.date_acquired).toLocaleDateString('en-IN') : '-'}
                                                    </td>
                                                    <td className="p-2 text-right dark:text-gray-300">
                                                        {formatCurrency2(entry.initial_value, entry.currency)}
                                                    </td>
                                                    <td className="p-2 text-right text-green-600 font-medium">
                                                        <div>{formatCurrency2(entry.peak_value, entry.currency)}</div>
                                                        {entry.peak_value_date && (
                                                            <div className="text-xs text-gray-500 font-normal">
                                                                on {new Date(entry.peak_value_date).toLocaleDateString('en-IN')}
                                                            </div>
                                                        )}
                                                    </td>
                                                    <td className="p-2 text-right dark:text-gray-300">
                                                        {formatCurrency2(entry.closing_value, entry.currency)}
                                                    </td>
                                                    <td className="p-2 text-right dark:text-gray-300">
                                                        {formatCurrency2(entry.gross_amount_received, entry.currency)}
                                                    </td>
                                                    <td className="p-2 text-right dark:text-gray-300">
                                                        {formatCurrency2(entry.gross_proceeds_from_sale, entry.currency)}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </>
                    )}
                </>
            )}
        </div>
    );
};

export default CapitalGainsPage;
