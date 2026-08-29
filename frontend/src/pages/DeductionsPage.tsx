import React, { useEffect, useState, useCallback } from 'react';
import { usePrivacy } from '../context/PrivacyContext';
import { getCurrentFinancialYear, getFinancialYearOptions } from '../utils/formatting';
import { DeductionEntryModal } from '../components/DeductionEntryModal';
import {
  createTaxDeduction,
  deleteTaxDeduction,
  getTaxDeductions,
  getTaxDeductionsSummary,
  updateTaxDeduction,
} from '../services/taxDeductionService';
import {
  TaxDeduction,
  TaxDeductionCreate,
  TaxDeductionFYSummary,
} from '../types/tax_deduction';

const SECTION_COLOR_MAP: Record<string, { bg: string; bar: string; text: string }> = {
  '80C': {
    bg: 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800',
    bar: 'bg-blue-600 dark:bg-blue-500',
    text: 'text-blue-700 dark:text-blue-300',
  },
  '80D': {
    bg: 'bg-teal-50 dark:bg-teal-900/30 border-teal-200 dark:border-teal-800',
    bar: 'bg-teal-600 dark:bg-teal-500',
    text: 'text-teal-700 dark:text-teal-300',
  },
  '80CCD_1B': {
    bg: 'bg-purple-50 dark:bg-purple-900/30 border-purple-200 dark:border-purple-800',
    bar: 'bg-purple-600 dark:bg-purple-500',
    text: 'text-purple-700 dark:text-purple-300',
  },
  '80TTA': {
    bg: 'bg-amber-50 dark:bg-amber-900/30 border-amber-200 dark:border-amber-800',
    bar: 'bg-amber-600 dark:bg-amber-500',
    text: 'text-amber-700 dark:text-amber-300',
  },
  '80TTB': {
    bg: 'bg-amber-50 dark:bg-amber-900/30 border-amber-200 dark:border-amber-800',
    bar: 'bg-amber-600 dark:bg-amber-500',
    text: 'text-amber-700 dark:text-amber-300',
  },
  DEFAULT: {
    bg: 'bg-slate-50 dark:bg-slate-900/30 border-slate-200 dark:border-slate-800',
    bar: 'bg-slate-600 dark:bg-slate-500',
    text: 'text-slate-700 dark:text-slate-300',
  },
};

export const DeductionsPage: React.FC = () => {
  const [selectedFY, setSelectedFY] = useState<string>(getCurrentFinancialYear());
  const [selectedSectionFilter, setSelectedSectionFilter] = useState<string>('');
  const fyOptions = getFinancialYearOptions();


  const [deductions, setDeductions] = useState<TaxDeduction[]>([]);
  const [summary, setSummary] = useState<TaxDeductionFYSummary | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingDeduction, setEditingDeduction] = useState<TaxDeduction | null>(null);

  const { isPrivacyMode } = usePrivacy();

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [listRes, summaryRes] = await Promise.all([
        getTaxDeductions(selectedFY, selectedSectionFilter || undefined),
        getTaxDeductionsSummary(selectedFY),
      ]);
      setDeductions(listRes);
      setSummary(summaryRes);
    } catch (err) {
      console.error('Failed to load tax deductions:', err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedFY, selectedSectionFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSave = async (data: TaxDeductionCreate, id?: string) => {
    if (id) {
      await updateTaxDeduction(id, data);
    } else {
      await createTaxDeduction(data);
    }
    fetchData();
  };

  const handleDelete = async (item: TaxDeduction) => {
    if (
      window.confirm(
        `Are you sure you want to delete deduction "${item.title}" (${item.section})?`
      )
    ) {
      await deleteTaxDeduction(item.id);
      fetchData();
    }
  };

  const formatAmount = (val: number | string) => {
    if (isPrivacyMode) return '****';
    const num = typeof val === 'number' ? val : parseFloat(val);
    return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const totalInvested = summary?.total_invested || 0;
  const totalEligible = summary?.total_eligible_deduction || 0;

  return (
    <div className="container mx-auto space-y-6 p-4 pt-safe md:p-6">
      {/* Header */}
      <div className="flex flex-col space-y-4 md:flex-row md:items-center md:justify-between md:space-y-0">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Tax Deductions & Chapter VI-A
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Log tax-deductible expenses & investments (80C, 80D, 80CCD, etc.) with statutory limit capping.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* FY Dropdown */}
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">FY:</span>
            <select
              value={selectedFY}
              onChange={(e) => setSelectedFY(e.target.value)}
              className="min-h-[44px] rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-900 shadow-sm dark:border-slate-600 dark:bg-slate-800 dark:text-white"
            >
              {fyOptions.map((fy) => (
                <option key={fy} value={fy}>
                  {fy}
                </option>
              ))}
            </select>

          </div>

          <button
            onClick={() => {
              setEditingDeduction(null);
              setIsModalOpen(true);
            }}
            className="min-h-[44px] rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
          >
            + Log Tax Deduction
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Total Claimed / Invested ({selectedFY})
          </span>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {formatAmount(totalInvested)}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
            Eligible Statutory Tax Deduction ({selectedFY})
          </span>
          <div className="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">
            {formatAmount(totalEligible)}
          </div>
        </div>
      </div>

      {/* Statutory Section Progress Meters */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <h2 className="mb-4 text-lg font-bold text-slate-900 dark:text-white">
          Statutory Section Limits & Progress
        </h2>

        {summary?.sections && summary.sections.length > 0 ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {summary.sections.map((sec) => {
              const colorInfo = SECTION_COLOR_MAP[sec.section] || SECTION_COLOR_MAP.DEFAULT;
              const invested = sec.total_invested;
              const maxLimit = sec.max_limit;
              const pct = maxLimit ? Math.min(100, (invested / maxLimit) * 100) : 100;

              return (
                <div
                  key={sec.section}
                  className={`rounded-xl border p-4 shadow-sm ${colorInfo.bg}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 dark:text-white">
                      Section {sec.section}
                    </span>
                    <span className={`text-xs font-bold ${colorInfo.text}`}>
                      {maxLimit ? `Cap: ${formatAmount(maxLimit)}` : 'Uncapped'}
                    </span>
                  </div>
                  <div className="mt-1 text-xs text-slate-600 dark:text-slate-400 line-clamp-1">
                    {sec.section_name}
                  </div>

                  {/* Progress Bar */}
                  {maxLimit !== null && (
                    <div className="mt-3">
                      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${colorInfo.bar}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <div className="mt-1 flex justify-between text-[11px] font-medium text-slate-600 dark:text-slate-400">
                        <span>Invested: {formatAmount(invested)}</span>
                        <span>{pct.toFixed(0)}%</span>
                      </div>
                    </div>
                  )}

                  {maxLimit === null && (
                    <div className="mt-2 text-sm font-semibold text-slate-800 dark:text-slate-200">
                      Invested: {formatAmount(invested)}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="py-4 text-center text-sm text-slate-500">
            No statutory deductions logged yet for FY {selectedFY}.
          </div>
        )}
      </div>

      {/* Deductions Ledger Table */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div className="mb-4 flex flex-col space-y-3 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">
            Tax Deduction Entries ({deductions.length})
          </h2>

          {/* Section Filter */}
          <div className="flex items-center space-x-2">
            <span className="text-xs font-medium text-slate-500">Filter Section:</span>
            <select
              value={selectedSectionFilter}
              onChange={(e) => setSelectedSectionFilter(e.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-900 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
            >
              <option value="">All Sections</option>
              <option value="80C">Section 80C</option>
              <option value="80D">Section 80D</option>
              <option value="80CCD_1B">Section 80CCD(1B)</option>
              <option value="80TTA">Section 80TTA</option>
              <option value="80TTB">Section 80TTB</option>
              <option value="80G">Section 80G</option>
              <option value="80E">Section 80E</option>
              <option value="OTHER">Other</option>
            </select>
          </div>
        </div>

        {isLoading ? (
          <div className="py-8 text-center text-sm text-slate-500">Loading deductions...</div>
        ) : deductions.length === 0 ? (
          <div className="rounded-lg bg-slate-50 py-10 text-center text-slate-500 dark:bg-slate-900/50 dark:text-slate-400">
            No tax deductions logged for FY {selectedFY}. Click "+ Log Tax Deduction" above to add your first expense.
          </div>
        ) : (
          <>
            {/* Desktop Table View */}
            <div className="hidden overflow-x-auto lg:block">
              <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
                <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-900/50 dark:text-slate-400">
                  <tr>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3">Section</th>
                    <th className="px-4 py-3">Title / Description</th>
                    <th className="px-4 py-3 text-right">Amount</th>
                    <th className="px-4 py-3">Proof Notes</th>
                    <th className="px-4 py-3 text-center">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
                  {deductions.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/30">
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                        {item.deduction_date}
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-block rounded bg-blue-100 px-2 py-0.5 text-xs font-bold text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">
                          {item.section}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-semibold text-slate-800 dark:text-slate-200">
                        {item.title}
                      </td>
                      <td className="px-4 py-3 text-right font-bold text-slate-900 dark:text-white">
                        {formatAmount(item.amount)}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">
                        {item.proof_notes || '-'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <div className="flex items-center justify-center space-x-3">
                          <button
                            onClick={() => {
                              setEditingDeduction(item);
                              setIsModalOpen(true);
                            }}
                            className="text-xs font-medium text-blue-600 hover:underline dark:text-blue-400"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(item)}
                            className="text-xs font-medium text-red-600 hover:underline dark:text-red-400"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile Card Grid View (< 1024px) */}
            <div className="grid grid-cols-1 gap-3 lg:hidden">
              {deductions.map((item) => (
                <div
                  key={item.id}
                  className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800"
                >
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2 dark:border-slate-700">
                    <div>
                      <span className="inline-block rounded bg-blue-100 px-2 py-0.5 text-xs font-bold text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">
                        {item.section}
                      </span>
                      <span className="ml-2 text-xs text-slate-500">{item.deduction_date}</span>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => {
                          setEditingDeduction(item);
                          setIsModalOpen(true);
                        }}
                        className="text-xs font-medium text-blue-600 dark:text-blue-400"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(item)}
                        className="text-xs font-medium text-red-600 dark:text-red-400"
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  <div className="mt-3 flex items-center justify-between">
                    <div className="font-semibold text-slate-900 dark:text-white">{item.title}</div>
                    <div className="font-bold text-slate-900 dark:text-white">
                      {formatAmount(item.amount)}
                    </div>
                  </div>

                  {item.proof_notes && (
                    <div className="mt-2 text-xs italic text-slate-500 dark:text-slate-400">
                      Proof: "{item.proof_notes}"
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Modal */}
      <DeductionEntryModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSave}
        editingDeduction={editingDeduction}
        selectedFY={selectedFY}
      />
    </div>
  );
};

export default DeductionsPage;
