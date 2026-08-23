import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { CapitalLossLedgerEntry, useCapitalLossLedger } from '../../hooks/useCapitalGains';

interface CapitalLossLedgerModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentFy: string;
}

export const CapitalLossLedgerModal: React.FC<CapitalLossLedgerModalProps> = ({
  isOpen,
  onClose,
  currentFy,
}) => {
  const queryClient = useQueryClient();
  const { data: ledgerEntries = [], isLoading } = useCapitalLossLedger(currentFy);

  const [financialYear, setFinancialYear] = useState('2024-25');
  const [assessmentYear, setAssessmentYear] = useState('2025-26');
  const [stclAmount, setStclAmount] = useState<number>(0);
  const [ltclAmount, setLtclAmount] = useState<number>(0);
  const [isItrFiledOnTime, setIsItrFiledOnTime] = useState<boolean>(true);
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  if (!isOpen) return null;

  const handleAddEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg('');
    try {
      await api.post(`/api/v1/capital-gains/loss-ledger?current_fy=${currentFy}`, {
        financial_year: financialYear,
        assessment_year: assessmentYear,
        stcl_amount: stclAmount,
        ltcl_amount: ltclAmount,
        is_itr_filed_on_time: isItrFiledOnTime,
        notes: notes || undefined,
      });
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ['loss-ledger'] });
      queryClient.invalidateQueries({ queryKey: ['capital-setoff'] });
      // Reset form
      setStclAmount(0);
      setLtclAmount(0);
      setNotes('');
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } };
      setErrorMsg(error?.response?.data?.detail || 'Failed to add loss ledger entry.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteEntry = async (id: string) => {
    try {
      await api.delete(`/api/v1/capital-gains/loss-ledger/${id}`);
      queryClient.invalidateQueries({ queryKey: ['loss-ledger'] });
      queryClient.invalidateQueries({ queryKey: ['capital-setoff'] });
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } };
      alert(error?.response?.data?.detail || 'Failed to delete loss entry.');
    }
  };


  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl w-full max-w-4xl p-6 text-slate-100">
        <div className="flex justify-between items-center pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <span>📋 Carry-Forward Capital Loss Ledger</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Track statutory brought-forward losses under Section 74 (8 Assessment Years limit).
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 text-lg p-2 rounded-lg hover:bg-slate-800 transition"
          >
            ✕
          </button>
        </div>

        {/* Existing Entries Table */}
        <div className="my-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">
            Brought-Forward Loss Records
          </h3>
          {isLoading ? (
            <div className="text-center py-6 text-slate-400">Loading ledger records...</div>
          ) : ledgerEntries.length === 0 ? (
            <div className="text-center py-6 bg-slate-950/50 rounded-lg border border-slate-800/80 text-slate-400 text-sm">
              No brought-forward capital loss records found. Use the form below to add loss entries from previous ITR filings.
            </div>
          ) : (
            <div className="overflow-x-auto border border-slate-800 rounded-lg">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-3">Loss FY / AY</th>
                    <th className="p-3 text-right">STCL (₹)</th>
                    <th className="p-3 text-right">LTCL (₹)</th>
                    <th className="p-3 text-center">Filed On Time</th>
                    <th className="p-3 text-center">8-Year Meter</th>
                    <th className="p-3 text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {ledgerEntries.map((entry: CapitalLossLedgerEntry) => (
                    <tr key={entry.id} className="hover:bg-slate-800/50">
                      <td className="p-3 font-medium">
                        <div>FY {entry.financial_year}</div>
                        <div className="text-[10px] text-slate-400">AY {entry.assessment_year}</div>
                      </td>
                      <td className="p-3 text-right text-rose-400 font-mono">
                        ₹{entry.stcl_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="p-3 text-right text-rose-400 font-mono">
                        ₹{entry.ltcl_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="p-3 text-center">
                        {entry.is_itr_filed_on_time ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                            Yes (Eligible)
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-950 text-rose-400 border border-rose-800">
                            No (Disallowed)
                          </span>
                        )}
                      </td>
                      <td className="p-3 text-center">
                        {entry.is_expired ? (
                          <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400 border border-slate-700">
                            Expired
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-cyan-950 text-cyan-300 border border-cyan-800">
                            {entry.years_remaining} AY Remaining
                          </span>
                        )}
                      </td>
                      <td className="p-3 text-center">
                        <button
                          onClick={() => handleDeleteEntry(entry.id)}
                          className="text-rose-400 hover:text-rose-300 p-1 hover:bg-rose-950/50 rounded"
                          title="Delete entry"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Add Entry Form */}
        <form onSubmit={handleAddEntry} className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
          <h3 className="text-xs font-semibold text-slate-300 mb-3 flex items-center gap-1">
            <span>➕ Add Brought-Forward Loss Record</span>
          </h3>

          {errorMsg && (
            <div className="mb-3 p-2 text-xs bg-rose-950/80 border border-rose-800 text-rose-300 rounded">
              {errorMsg}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs mb-3">
            <div>
              <label className="block text-slate-400 mb-1">Financial Year (FY)</label>
              <input
                type="text"
                value={financialYear}
                onChange={(e) => {
                  setFinancialYear(e.target.value);
                  const parts = e.target.value.split('-');
                  if (parts.length > 0 && !isNaN(Number(parts[0]))) {
                    const y = Number(parts[0]) + 1;
                    setAssessmentYear(`${y}-${(y + 1) % 100}`);
                  }
                }}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-slate-100 focus:outline-none focus:border-cyan-500"
                placeholder="2024-25"
                required
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Assessment Year (AY)</label>
              <input
                type="text"
                value={assessmentYear}
                onChange={(e) => setAssessmentYear(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-slate-100 focus:outline-none focus:border-cyan-500"
                placeholder="2025-26"
                required
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">ITR Filed On Time (Sec 139(1))</label>
              <select
                value={isItrFiledOnTime ? 'true' : 'false'}
                onChange={(e) => setIsItrFiledOnTime(e.target.value === 'true')}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-slate-100 focus:outline-none focus:border-cyan-500"
              >
                <option value="true">Yes (On or before due date)</option>
                <option value="false">No (Belated return - Loss disallowed)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs mb-4">
            <div>
              <label className="block text-slate-400 mb-1">STCL Amount (₹)</label>
              <input
                type="number"
                step="0.01"
                value={stclAmount}
                onChange={(e) => setStclAmount(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">LTCL Amount (₹)</label>
              <input
                type="number"
                step="0.01"
                value={ltclAmount}
                onChange={(e) => setLtclAmount(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Notes / ITR Ref (Optional)</label>
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-slate-100 focus:outline-none focus:border-cyan-500"
                placeholder="e.g. ITR-2 Ack #12345"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 rounded hover:bg-slate-800 transition"
            >
              Close
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white rounded shadow transition disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : 'Save Loss Entry'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
