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

  // Salary breakdown state
  const [showSalaryDrawer, setShowSalaryDrawer] = useState(false);
  const [basicAmount, setBasicAmount] = useState('');
  const [hraAmount, setHraAmount] = useState('');
  const [daAmount, setDaAmount] = useState('');
  const [specialAllowance, setSpecialAllowance] = useState('');
  const [otherAllowances, setOtherAllowances] = useState('');
  const [otherBenefits, setOtherBenefits] = useState('');
  const [rentPaid, setRentPaid] = useState('');
  const [isMetro, setIsMetro] = useState(false);

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

      setBasicAmount(initialEntry.basic_amount !== null && initialEntry.basic_amount !== undefined ? String(initialEntry.basic_amount) : '');
      setHraAmount(initialEntry.hra_amount !== null && initialEntry.hra_amount !== undefined ? String(initialEntry.hra_amount) : '');
      setDaAmount(initialEntry.da_amount !== null && initialEntry.da_amount !== undefined ? String(initialEntry.da_amount) : '');
      setSpecialAllowance(initialEntry.special_allowance_amount !== null && initialEntry.special_allowance_amount !== undefined ? String(initialEntry.special_allowance_amount) : '');
      setOtherAllowances(initialEntry.other_allowances_amount !== null && initialEntry.other_allowances_amount !== undefined ? String(initialEntry.other_allowances_amount) : '');
      setOtherBenefits(initialEntry.other_benefits_amount !== null && initialEntry.other_benefits_amount !== undefined ? String(initialEntry.other_benefits_amount) : '');
      setRentPaid(initialEntry.rent_paid !== null && initialEntry.rent_paid !== undefined ? String(initialEntry.rent_paid) : '');
      setIsMetro(Boolean(initialEntry.is_metro));

      const hasSalaryData = Boolean(
        initialEntry.basic_amount ||
        initialEntry.hra_amount ||
        initialEntry.da_amount ||
        initialEntry.special_allowance_amount ||
        initialEntry.other_allowances_amount ||
        initialEntry.other_benefits_amount ||
        initialEntry.rent_paid
      );
      setShowSalaryDrawer(hasSalaryData);
    } else {
      const defaultSource = sources.length > 0 ? sources[0] : null;
      setSourceId(defaultSource ? defaultSource.id : '');
      setFinancialYear(selectedFY);
      setEntryDate(new Date().toISOString().split('T')[0]);
      setGrossAmount('');
      setTdsAmount('0');
      setNotes('');

      setBasicAmount('');
      setHraAmount('');
      setDaAmount('');
      setSpecialAllowance('');
      setOtherAllowances('');
      setOtherBenefits('');
      setRentPaid('');
      setIsMetro(false);
      setShowSalaryDrawer(defaultSource?.category === 'SALARY');
    }
    setError(null);
  }, [initialEntry, isOpen, sources, selectedFY]);

  if (!isOpen) return null;

  const selectedSource = sources.find((s) => s.id === sourceId);
  const isSalary = selectedSource?.category === 'SALARY';

  const grossVal = parseFloat(grossAmount) || 0;
  const tdsVal = parseFloat(tdsAmount) || 0;
  const netVal = Math.max(0, grossVal - tdsVal);

  const basicVal = parseFloat(basicAmount) || 0;
  const hraVal = parseFloat(hraAmount) || 0;
  const daVal = parseFloat(daAmount) || 0;
  const rentVal = parseFloat(rentPaid) || 0;

  // Live Section 10(13A) HRA exemption math preview
  const basicDa = basicVal + daVal;
  let computedHraExemption = 0;
  if (hraVal > 0 && rentVal > 0 && basicDa > 0) {
    const opt1 = hraVal;
    const opt2 = rentVal - 0.10 * basicDa;
    const opt3 = (isMetro ? 0.50 : 0.40) * basicDa;
    computedHraExemption = Math.max(0, Math.min(opt1, opt2, opt3));
  }
  const netTaxableSalary = Math.max(0, grossVal - computedHraExemption);

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

    if (showSalaryDrawer) {
      if (basicVal > grossVal) {
        setError('Basic Salary cannot exceed Gross Income Amount.');
        return;
      }
      if (hraVal > grossVal) {
        setError('HRA Received cannot exceed Gross Income Amount.');
        return;
      }
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
          basic_amount: showSalaryDrawer && basicAmount !== '' ? basicVal : undefined,
          hra_amount: showSalaryDrawer && hraAmount !== '' ? hraVal : undefined,
          da_amount: showSalaryDrawer && daAmount !== '' ? daVal : undefined,
          special_allowance_amount: showSalaryDrawer && specialAllowance !== '' ? (parseFloat(specialAllowance) || 0) : undefined,
          other_allowances_amount: showSalaryDrawer && otherAllowances !== '' ? (parseFloat(otherAllowances) || 0) : undefined,
          other_benefits_amount: showSalaryDrawer && otherBenefits !== '' ? (parseFloat(otherBenefits) || 0) : undefined,
          rent_paid: showSalaryDrawer && rentPaid !== '' ? rentVal : undefined,
          is_metro: showSalaryDrawer ? isMetro : false,
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
      <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-xl bg-white p-6 shadow-xl dark:bg-slate-800">
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
              onChange={(e) => {
                const sId = e.target.value;
                setSourceId(sId);
                const s = sources.find((src) => src.id === sId);
                if (s?.category === 'SALARY') {
                  setShowSalaryDrawer(true);
                }
              }}
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

          {/* Salary Breakdown & HRA Calculator Drawer Toggle */}
          <div className="pt-2">
            <button
              type="button"
              onClick={() => setShowSalaryDrawer(!showSalaryDrawer)}
              className="flex items-center space-x-2 text-sm font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              <span>{showSalaryDrawer ? '▼ Hide' : '► Include'} Salary Breakdown & Sec 10(13A) HRA Exemption</span>
              {isSalary && <span className="rounded bg-indigo-100 dark:bg-indigo-900/50 px-2 py-0.5 text-xs text-indigo-700 dark:text-indigo-300 font-medium">Recommended for Salary</span>}
            </button>

            {showSalaryDrawer && (
              <div className="mt-3 rounded-lg border border-indigo-100 bg-indigo-50/50 p-4 dark:border-slate-700 dark:bg-slate-800/80 space-y-4">
                <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
                  Salary Component Breakdown
                </h3>

                <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                      Basic Salary (₹)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      inputMode="decimal"
                      placeholder="50000"
                      value={basicAmount}
                      onChange={(e) => setBasicAmount(e.target.value)}
                      className="mt-1 block w-full min-h-[40px] rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                      HRA Received (₹)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      inputMode="decimal"
                      placeholder="25000"
                      value={hraAmount}
                      onChange={(e) => setHraAmount(e.target.value)}
                      className="mt-1 block w-full min-h-[40px] rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                      Dearness Allowance (DA) (₹)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      inputMode="decimal"
                      placeholder="0"
                      value={daAmount}
                      onChange={(e) => setDaAmount(e.target.value)}
                      className="mt-1 block w-full min-h-[40px] rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                      Flexible / Special Allowance (₹)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      inputMode="decimal"
                      placeholder="15000"
                      value={specialAllowance}
                      onChange={(e) => setSpecialAllowance(e.target.value)}
                      className="mt-1 block w-full min-h-[40px] rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                      Other Allowances (₹)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      inputMode="decimal"
                      placeholder="5000"
                      value={otherAllowances}
                      onChange={(e) => setOtherAllowances(e.target.value)}
                      className="mt-1 block w-full min-h-[40px] rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                      Other Benefits / Perquisites (₹)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      inputMode="decimal"
                      placeholder="5000"
                      value={otherBenefits}
                      onChange={(e) => setOtherBenefits(e.target.value)}
                      className="mt-1 block w-full min-h-[40px] rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
                    />
                  </div>
                </div>

                <div className="border-t border-indigo-200/60 dark:border-slate-700 pt-3">
                  <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-2">
                    Rent Paid & Location (HRA Exemption Calculation)
                  </h4>
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 items-center">
                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                        Rent Paid (₹)
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        inputMode="decimal"
                        placeholder="20000"
                        value={rentPaid}
                        onChange={(e) => setRentPaid(e.target.value)}
                        className="mt-1 block w-full min-h-[40px] rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
                      />
                    </div>

                    <div className="flex items-center space-x-2 pt-4">
                      <input
                        type="checkbox"
                        id="isMetro"
                        checked={isMetro}
                        onChange={(e) => setIsMetro(e.target.checked)}
                        className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-700"
                      />
                      <label htmlFor="isMetro" className="text-xs font-medium text-slate-700 dark:text-slate-300 cursor-pointer">
                        Metro City (Mumbai, Delhi, Kolkata, Chennai - 50% Basic Cap)
                      </label>
                    </div>
                  </div>
                </div>

                {/* Calculation Summary Box */}
                <div className="rounded-lg bg-emerald-50 dark:bg-emerald-950/30 p-3 border border-emerald-200 dark:border-emerald-800/50 text-xs text-emerald-900 dark:text-emerald-300 space-y-1">
                  <div className="flex justify-between font-medium">
                    <span>Computed Sec 10(13A) HRA Exemption:</span>
                    <span className="font-bold">₹{computedHraExemption.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between font-medium pt-1 border-t border-emerald-200/50 dark:border-emerald-800/30">
                    <span>Estimated Net Taxable Salary:</span>
                    <span className="font-bold">₹{netTaxableSalary.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>
                </div>
              </div>
            )}
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

