import React, { useEffect, useState } from 'react';
import { getFinancialYearOptions } from '../utils/formatting';
import { IncomeEntry, IncomeEntryPayload, IncomeSource } from '../types/income';


interface IncomeEntryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (payload: IncomeEntryPayload, entryId?: string) => Promise<void>;
  sources: IncomeSource[];
  selectedFY: string;
  initialEntry?: IncomeEntry | null;
}

export const IncomeEntryModal: React.FC<IncomeEntryModalProps> = ({
  isOpen,
  onClose,
  onSave,
  sources,
  selectedFY,
  initialEntry,
}) => {
  const [sourceId, setSourceId] = useState('');
  const [financialYear, setFinancialYear] = useState(selectedFY);
  const [entryDate, setEntryDate] = useState(new Date().toISOString().split('T')[0]);
  const [grossAmount, setGrossAmount] = useState('');
  const [tdsAmount, setTdsAmount] = useState('0');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialEntry) {
      setSourceId(initialEntry.source_id);
      setFinancialYear(initialEntry.financial_year);
      setEntryDate(initialEntry.entry_date);
      setGrossAmount(String(initialEntry.gross_amount));
      setTdsAmount(String(initialEntry.tds_amount));
      setNotes(initialEntry.notes || '');
    } else {
      setSourceId(sources.length > 0 ? sources[0].id : '');
      setFinancialYear(selectedFY);
      setEntryDate(new Date().toISOString().split('T')[0]);
      setGrossAmount('');
      setTdsAmount('0');
      setNotes('');
    }
    setError(null);
  }, [initialEntry, isOpen, sources, selectedFY]);

  if (!isOpen) return null;

  const grossVal = parseFloat(grossAmount) || 0;
  const tdsVal = parseFloat(tdsAmount) || 0;
  const netVal = Math.max(0, grossVal - tdsVal);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceId) {
      setError('Please select an income source.');
      return;
    }
    if (grossVal <= 0) {
      setError('Gross Amount must be greater than 0.');
      return;
    }
    if (tdsVal < 0) {
      setError('TDS Amount cannot be negative.');
      return;
    }
    if (tdsVal > grossVal) {
      setError('TDS Amount cannot exceed Gross Income Amount.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onSave(
        {
          source_id: sourceId,
          financial_year: financialYear,
          entry_date: entryDate,
          gross_amount: grossVal,
          tds_amount: tdsVal,
          notes: notes.trim() || undefined,
        },
        initialEntry?.id
      );
      onClose();
    } catch (err: unknown) {
      const errorMsg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Failed to save income entry.';
      setError(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl dark:bg-slate-800">
        <h2 className="mb-4 text-xl font-bold text-slate-900 dark:text-white">
          {initialEntry ? 'Edit Income Entry' : 'Log Income Entry'}
        </h2>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Income Source *
            </label>
            <select
              required
              value={sourceId}
              onChange={(e) => setSourceId(e.target.value)}
              className="mt-1 block w-full min-h-[44px] rounded-lg border border-slate-300 px-3 py-2 text-slate-900 focus:border-indigo-500 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
            >
              <option value="" disabled>
                Select Source...
              </option>
              {sources.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.category})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Financial Year *
              </label>
              <select
                required
                value={financialYear}
                onChange={(e) => setFinancialYear(e.target.value)}
                className="mt-1 block w-full min-h-[44px] rounded-lg border border-slate-300 px-3 py-2 text-slate-900 focus:border-indigo-500 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
              >
                {getFinancialYearOptions().map((fy) => (
                  <option key={fy} value={fy}>
                    {fy}
                  </option>
                ))}
              </select>

            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Entry Date *
              </label>
              <input
                type="date"
                required
                value={entryDate}
                onChange={(e) => setEntryDate(e.target.value)}
                className="mt-1 block w-full min-h-[44px] rounded-lg border border-slate-300 px-3 py-2 text-slate-900 focus:border-indigo-500 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Gross Amount (₹) *
              </label>
              <input
                type="number"
                step="0.01"
                required
                inputMode="decimal"
                placeholder="100000"
                value={grossAmount}
                onChange={(e) => setGrossAmount(e.target.value)}
                className="mt-1 block w-full min-h-[44px] rounded-lg border border-slate-300 px-3 py-2 text-slate-900 focus:border-indigo-500 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                TDS Deducted (₹)
              </label>
              <input
                type="number"
                step="0.01"
                inputMode="decimal"
                placeholder="10000"
                value={tdsAmount}
                onChange={(e) => setTdsAmount(e.target.value)}
                className="mt-1 block w-full min-h-[44px] rounded-lg border border-slate-300 px-3 py-2 text-slate-900 focus:border-indigo-500 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Net Received (₹)
              </label>
              <div className="mt-1 flex min-h-[44px] items-center rounded-lg bg-slate-100 px-3 py-2 text-base font-semibold text-emerald-600 dark:bg-slate-700/50 dark:text-emerald-400">
                ₹{netVal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Notes (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. May 2025 Monthly Salary"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-1 block w-full min-h-[44px] rounded-lg border border-slate-300 px-3 py-2 text-slate-900 focus:border-indigo-500 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
            />
          </div>

          <div className="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : initialEntry ? 'Update Entry' : 'Log Entry'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
