import React, { useState } from 'react';
import {
  useCreateIncomeEntry,
  useCreateIncomeSource,
  useDeleteIncomeEntry,
  useDeleteIncomeSource,
  useIncomeEntries,
  useIncomeSources,
  useIncomeSummary,
  useUpdateIncomeEntry,
  useUpdateIncomeSource,
} from '../hooks/useIncome';
import { usePrivacy } from '../context/PrivacyContext';
import { IncomeEntry, IncomeEntryPayload, IncomeSource, IncomeSourcePayload } from '../types/income';
import { IncomeSourceModal } from '../components/IncomeSourceModal';
import { IncomeEntryModal } from '../components/IncomeEntryModal';

import { getCurrentFinancialYear, getFinancialYearOptions } from '../utils/formatting';
import DeductionsPage from './DeductionsPage';

export const IncomePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'income' | 'deductions'>('income');
  const [selectedFY, setSelectedFY] = useState<string>(getCurrentFinancialYear());
  const [selectedSourceFilter, setSelectedSourceFilter] = useState<string>('');
  const fyOptions = getFinancialYearOptions();


  // Modals state
  const [isSourceModalOpen, setIsSourceModalOpen] = useState(false);
  const [editingSource, setEditingSource] = useState<IncomeSource | null>(null);

  const [isEntryModalOpen, setIsEntryModalOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState<IncomeEntry | null>(null);

  const { isPrivacyMode } = usePrivacy();

  // React Query Hooks
  const { data: sources = [], isLoading: isLoadingSources } = useIncomeSources();
  const { data: entries = [], isLoading: isLoadingEntries } = useIncomeEntries(
    selectedFY,
    selectedSourceFilter || undefined
  );
  const { data: summary } = useIncomeSummary(selectedFY);

  const createSourceMutation = useCreateIncomeSource();
  const updateSourceMutation = useUpdateIncomeSource();
  const deleteSourceMutation = useDeleteIncomeSource();

  const createEntryMutation = useCreateIncomeEntry();
  const updateEntryMutation = useUpdateIncomeEntry();
  const deleteEntryMutation = useDeleteIncomeEntry();

  // Handlers for Sources
  const handleSaveSource = async (payload: IncomeSourcePayload, sourceId?: string) => {
    if (sourceId) {
      await updateSourceMutation.mutateAsync({ id: sourceId, payload });
    } else {
      await createSourceMutation.mutateAsync(payload);
    }
  };

  const handleDeleteSource = async (source: IncomeSource) => {
    if (
      window.confirm(
        `Are you sure you want to delete source "${source.name}"? All associated income entries will be deleted.`
      )
    ) {
      await deleteSourceMutation.mutateAsync(source.id);
    }
  };

  // Handlers for Entries
  const handleSaveEntry = async (payload: IncomeEntryPayload, entryId?: string) => {
    if (entryId) {
      await updateEntryMutation.mutateAsync({ id: entryId, payload });
    } else {
      await createEntryMutation.mutateAsync(payload);
    }
  };

  const handleDeleteEntry = async (entry: IncomeEntry) => {
    if (window.confirm('Are you sure you want to delete this income entry?')) {
      await deleteEntryMutation.mutateAsync(entry.id);
    }
  };

  const formatAmount = (val: number) => {
    if (isPrivacyMode) return '****';
    return `₹${val.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
  };

  const totalGross = summary?.total_gross || 0;
  const totalTds = summary?.total_tds || 0;
  const totalNet = summary?.total_net || 0;

  return (
    <div className="container mx-auto space-y-6 p-4 pt-safe md:p-6">
      {/* Top Tab Bar Navigation */}
      <div className="flex border-b border-slate-200 dark:border-slate-700">
        <button
          onClick={() => setActiveTab('income')}
          className={`px-5 py-3 text-sm font-bold transition-colors border-b-2 ${
            activeTab === 'income'
              ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
          }`}
        >
          Income & TDS Ledger
        </button>
        <button
          onClick={() => setActiveTab('deductions')}
          className={`px-5 py-3 text-sm font-bold transition-colors border-b-2 ${
            activeTab === 'deductions'
              ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
          }`}
        >
          Tax Deductions (Chapter VI-A)
        </button>
      </div>

      {activeTab === 'deductions' ? (
        <DeductionsPage />
      ) : (
        <>
          {/* Header */}
          <div className="flex flex-col space-y-4 md:flex-row md:items-center md:justify-between md:space-y-0">
            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                Income & TDS Data Management
              </h1>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Log salary, freelance income, rental yield, and track Tax Deducted at Source (TDS).
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
              setEditingSource(null);
              setIsSourceModalOpen(true);
            }}
            className="min-h-[44px] rounded-lg border border-indigo-600 px-4 py-2 text-sm font-medium text-indigo-600 hover:bg-indigo-50 dark:border-indigo-400 dark:text-indigo-400 dark:hover:bg-indigo-950/50"
          >
            + Add Source
          </button>

          <button
            onClick={() => {
              setEditingEntry(null);
              setIsEntryModalOpen(true);
            }}
            className="min-h-[44px] rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600"
          >
            + Log Income Entry
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Gross Income ({selectedFY})
          </span>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {formatAmount(totalGross)}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <span className="text-xs font-semibold uppercase tracking-wider text-amber-600 dark:text-amber-400">
            TDS Credited ({selectedFY})
          </span>
          <div className="mt-2 text-2xl font-bold text-amber-600 dark:text-amber-400">
            {formatAmount(totalTds)}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
            Net Received ({selectedFY})
          </span>
          <div className="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">
            {formatAmount(totalNet)}
          </div>
        </div>
      </div>

      {/* Income Sources Bar */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <h2 className="mb-4 text-lg font-bold text-slate-900 dark:text-white">
          Defined Income Sources ({sources.length})
        </h2>

        {isLoadingSources ? (
          <div className="py-4 text-center text-sm text-slate-500">Loading sources...</div>
        ) : sources.length === 0 ? (
          <div className="rounded-lg bg-slate-50 p-6 text-center text-slate-500 dark:bg-slate-900/50 dark:text-slate-400">
            No income sources created yet. Click "+ Add Source" to define salary, freelance, or rental sources.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {sources.map((src) => (
              <div
                key={src.id}
                className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/50"
              >
                <div>
                  <div className="font-semibold text-slate-900 dark:text-white">{src.name}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    <span className="inline-block rounded bg-indigo-100 px-1.5 py-0.5 text-[10px] font-bold text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-300">
                      {src.category}
                    </span>
                    {src.payer_name && <span className="ml-2">• {src.payer_name}</span>}
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => {
                      setEditingSource(src);
                      setIsSourceModalOpen(true);
                    }}
                    className="text-xs text-indigo-600 hover:underline dark:text-indigo-400"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDeleteSource(src)}
                    className="text-xs text-red-600 hover:underline dark:text-red-400"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Income Entries Ledger */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div className="mb-4 flex flex-col space-y-3 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">
            Income Log Ledger ({entries.length})
          </h2>

          {/* Source Filter */}
          <div className="flex items-center space-x-2">
            <span className="text-xs font-medium text-slate-500">Filter Source:</span>
            <select
              value={selectedSourceFilter}
              onChange={(e) => setSelectedSourceFilter(e.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-900 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
            >
              <option value="">All Sources</option>
              {sources.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {isLoadingEntries ? (
          <div className="py-8 text-center text-sm text-slate-500">Loading entries...</div>
        ) : entries.length === 0 ? (
          <div className="rounded-lg bg-slate-50 py-10 text-center text-slate-500 dark:bg-slate-900/50 dark:text-slate-400">
            No income entries logged for FY {selectedFY}. Click "+ Log Income Entry" above to add your first transaction.
          </div>
        ) : (
          <>
            {/* Desktop Table View */}
            <div className="hidden overflow-x-auto lg:block">
              <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
                <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-900/50 dark:text-slate-400">
                  <tr>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3">Source</th>
                    <th className="px-4 py-3 text-right">Gross Amount</th>
                    <th className="px-4 py-3 text-right">TDS Credited</th>
                    <th className="px-4 py-3 text-right">Net Received</th>
                    <th className="px-4 py-3">Notes</th>
                    <th className="px-4 py-3 text-center">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
                  {entries.map((entry) => (
                    <tr key={entry.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/30">
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                        {entry.entry_date}
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-semibold text-slate-800 dark:text-slate-200">
                          {entry.source_name || 'Income Source'}
                        </span>
                        {entry.source_category && (
                          <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600 dark:bg-slate-700 dark:text-slate-300">
                            {entry.source_category}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right font-medium text-slate-900 dark:text-white">
                        {formatAmount(Number(entry.gross_amount))}
                      </td>
                      <td className="px-4 py-3 text-right font-medium text-amber-600 dark:text-amber-400">
                        {formatAmount(Number(entry.tds_amount))}
                      </td>
                      <td className="px-4 py-3 text-right font-bold text-emerald-600 dark:text-emerald-400">
                        {formatAmount(Number(entry.net_amount))}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">
                        {entry.notes || '-'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <div className="flex items-center justify-center space-x-2">
                          <button
                            onClick={() => {
                              setEditingEntry(entry);
                              setIsEntryModalOpen(true);
                            }}
                            className="text-xs text-indigo-600 hover:underline dark:text-indigo-400"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteEntry(entry)}
                            className="text-xs text-red-600 hover:underline dark:text-red-400"
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
              {entries.map((entry) => (
                <div
                  key={entry.id}
                  className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800"
                >
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2 dark:border-slate-700">
                    <div>
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {entry.source_name || 'Income Source'}
                      </div>
                      <div className="text-xs text-slate-500">{entry.entry_date}</div>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => {
                          setEditingEntry(entry);
                          setIsEntryModalOpen(true);
                        }}
                        className="text-xs font-medium text-indigo-600 dark:text-indigo-400"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteEntry(entry)}
                        className="text-xs font-medium text-red-600 dark:text-red-400"
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <span className="text-slate-400">Gross:</span>
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {formatAmount(Number(entry.gross_amount))}
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-400">TDS:</span>
                      <div className="font-semibold text-amber-600 dark:text-amber-400">
                        {formatAmount(Number(entry.tds_amount))}
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-400">Net Received:</span>
                      <div className="font-bold text-emerald-600 dark:text-emerald-400">
                        {formatAmount(Number(entry.net_amount))}
                      </div>
                    </div>
                  </div>

                  {entry.notes && (
                    <div className="mt-2 text-xs italic text-slate-500 dark:text-slate-400">
                      "{entry.notes}"
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Modals */}
      <IncomeSourceModal
        isOpen={isSourceModalOpen}
        onClose={() => setIsSourceModalOpen(false)}
        onSave={handleSaveSource}
        initialSource={editingSource}
      />

      <IncomeEntryModal
        isOpen={isEntryModalOpen}
        onClose={() => setIsEntryModalOpen(false)}
        onSave={handleSaveEntry}
        sources={sources}
        selectedFY={selectedFY}
        initialEntry={editingEntry}
      />
        </>
      )}
    </div>
  );
};


export default IncomePage;
