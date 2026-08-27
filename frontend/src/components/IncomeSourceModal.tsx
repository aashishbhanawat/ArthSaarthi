import React, { useEffect, useState } from 'react';
import { IncomeCategory, IncomeSource, IncomeSourcePayload } from '../types/income';

interface IncomeSourceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (payload: IncomeSourcePayload, sourceId?: string) => Promise<void>;
  initialSource?: IncomeSource | null;
}

const CATEGORIES: { value: IncomeCategory; label: string }[] = [
  { value: 'SALARY', label: 'Salary / Compensation' },
  { value: 'FREELANCE', label: 'Freelance / Consulting' },
  { value: 'RENTAL', label: 'Rental Income' },
  { value: 'DIVIDEND', label: 'Dividends' },
  { value: 'INTEREST', label: 'Bank / FD Interest' },
  { value: 'BUSINESS', label: 'Business Profits' },
  { value: 'OTHER', label: 'Other Income' },
];

export const IncomeSourceModal: React.FC<IncomeSourceModalProps> = ({
  isOpen,
  onClose,
  onSave,
  initialSource,
}) => {
  const [name, setName] = useState('');
  const [category, setCategory] = useState<IncomeCategory>('SALARY');
  const [payerName, setPayerName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialSource) {
      setName(initialSource.name);
      setCategory(initialSource.category);
      setPayerName(initialSource.payer_name || '');
    } else {
      setName('');
      setCategory('SALARY');
      setPayerName('');
    }
    setError(null);
  }, [initialSource, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Please provide a name for this income source.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onSave(
        {
          name: name.trim(),
          category,
          payer_name: payerName.trim() || undefined,
        },
        initialSource?.id
      );
      onClose();
    } catch (err: unknown) {
      const errorMsg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Failed to save income source.';
      setError(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-slate-800">
        <h2 className="mb-4 text-xl font-bold text-slate-900 dark:text-white">
          {initialSource ? 'Edit Income Source' : 'Add Income Source'}
        </h2>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Source Name *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Primary Tech Salary, Freelance Work"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 block w-full min-h-[44px] rounded-lg border border-slate-300 px-3 py-2 text-slate-900 focus:border-indigo-500 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Income Category *
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as IncomeCategory)}
              className="mt-1 block w-full min-h-[44px] rounded-lg border border-slate-300 px-3 py-2 text-slate-900 focus:border-indigo-500 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Payer / Employer Name (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. Acme Corp, Client Name"
              value={payerName}
              onChange={(e) => setPayerName(e.target.value)}
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
              {isSubmitting ? 'Saving...' : initialSource ? 'Update Source' : 'Create Source'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
