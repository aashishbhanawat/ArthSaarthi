import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { TaxDeduction, TaxDeductionCreate } from '../types/tax_deduction';

interface DeductionEntryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: TaxDeductionCreate, id?: string) => Promise<void>;
  editingDeduction?: TaxDeduction | null;
  selectedFY: string;
}

const SECTION_OPTIONS = [
  { value: '80C', label: 'Section 80C (PPF, ELSS, EPF, LIC, NPS, Tuition Fee)' },
  { value: '80D', label: 'Section 80D (Health Insurance & Medical Checkup)' },
  { value: '80CCD_1B', label: 'Section 80CCD(1B) (NPS Additional Contribution)' },
  { value: '80TTA', label: 'Section 80TTA (Savings Account Interest)' },
  { value: '80TTB', label: 'Section 80TTB (Senior Citizen Interest)' },
  { value: '80G', label: 'Section 80G (Donations to Charitable Funds)' },
  { value: '80E', label: 'Section 80E (Education Loan Interest)' },
  { value: 'OTHER', label: 'Other Chapter VI-A Deductions' },
];

export const DeductionEntryModal: React.FC<DeductionEntryModalProps> = ({
  isOpen,
  onClose,
  onSave,
  editingDeduction,
  selectedFY,
}) => {
  const [financialYear, setFinancialYear] = useState<string>(selectedFY);
  const [section, setSection] = useState<string>('80C');
  const [title, setTitle] = useState<string>('');
  const [amount, setAmount] = useState<string>('');
  const [deductionDate, setDeductionDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [proofNotes, setProofNotes] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (editingDeduction) {
      setFinancialYear(editingDeduction.financial_year);
      setSection(editingDeduction.section);
      setTitle(editingDeduction.title);
      setAmount(editingDeduction.amount.toString());
      setDeductionDate(editingDeduction.deduction_date);
      setProofNotes(editingDeduction.proof_notes || '');
    } else {
      setFinancialYear(selectedFY);
      setSection('80C');
      setTitle('');
      setAmount('');
      setDeductionDate(new Date().toISOString().split('T')[0]);
      setProofNotes('');
    }
    setError('');
  }, [editingDeduction, selectedFY, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      setError('Please enter a valid amount greater than 0');
      return;
    }

    if (!title.trim()) {
      setError('Please enter a title/description');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSave(
        {
          financial_year: financialYear,
          section,
          title: title.trim(),
          amount: parsedAmount,
          deduction_date: deductionDate,
          proof_notes: proofNotes.trim() || undefined,
        },
        editingDeduction?.id
      );
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to save deduction entry');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl max-w-lg w-full p-6 shadow-xl border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between border-b pb-3 border-gray-200 dark:border-gray-700 mb-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            {editingDeduction ? 'Edit Tax Deduction' : 'Log Tax Deduction'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 p-1 rounded-lg"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm rounded-lg border border-red-200 dark:border-red-800">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Financial Year
            </label>
            <select
              value={financialYear}
              onChange={(e) => setFinancialYear(e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 p-2.5 min-h-[44px] text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value="2026-2027">2026-2027</option>
              <option value="2025-2026">2025-2026</option>
              <option value="2024-2025">2024-2025</option>
              <option value="2023-2024">2023-2024</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Deduction Section
            </label>
            <select
              value={section}
              onChange={(e) => setSection(e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 p-2.5 min-h-[44px] text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              {SECTION_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Title / Description
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. PPF Deposit, Health Insurance Policy"
              required
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 p-2.5 min-h-[44px] text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Amount (₹)
            </label>
            <input
              type="number"
              inputMode="decimal"
              step="any"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="e.g. 50000"
              required
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 p-2.5 min-h-[44px] text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Payment / Investment Date
            </label>
            <input
              type="date"
              value={deductionDate}
              onChange={(e) => setDeductionDate(e.target.value)}
              required
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 p-2.5 min-h-[44px] text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Proof Notes / Receipt Ref (Optional)
            </label>
            <input
              type="text"
              value={proofNotes}
              onChange={(e) => setProofNotes(e.target.value)}
              placeholder="e.g. Policy #98765432, Receipt uploaded"
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 p-2.5 min-h-[44px] text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium shadow-sm transition-colors disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : editingDeduction ? 'Update Deduction' : 'Save Deduction'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
