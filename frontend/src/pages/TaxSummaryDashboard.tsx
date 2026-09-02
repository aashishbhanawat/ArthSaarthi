import React, { useEffect, useState } from 'react';
import { TaxSummaryResponse } from '../types/tax_summary';
import {
  getTaxSummary,
  downloadExportCsv,
  downloadExportPdf,
} from '../services/taxSummaryService';
import { RegimeComparisonCard } from '../components/RegimeComparisonCard';
import { formatCurrency, getCurrentFinancialYear, getFinancialYearOptions } from '../utils/formatting';

export const TaxSummaryDashboard: React.FC = () => {
  const [financialYear, setFinancialYear] = useState<string>(getCurrentFinancialYear());
  const [summary, setSummary] = useState<TaxSummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isExportingCsv, setIsExportingCsv] = useState<boolean>(false);
  const [isExportingPdf, setIsExportingPdf] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const fyOptions = getFinancialYearOptions(new Date(), 6);

  const fetchSummary = async (fy: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await getTaxSummary(fy);
      setSummary(data);
    } catch (err: unknown) {
      const errorMsg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Failed to load tax summary.';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCsv = async () => {
    try {
      setIsExportingCsv(true);
      await downloadExportCsv(financialYear);
    } catch {
      alert('Failed to download CSV report. Please try again.');
    } finally {
      setIsExportingCsv(false);
    }
  };

  const handleExportPdf = async () => {
    try {
      setIsExportingPdf(true);
      await downloadExportPdf(financialYear);
    } catch {
      alert('Failed to download PDF report. Please try again.');
    } finally {
      setIsExportingPdf(false);
    }
  };

  useEffect(() => {
    fetchSummary(financialYear);
  }, [financialYear]);

  return (
    <div className="space-y-6 pb-12">
      {/* Top Title & Actions bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Tax Readiness Summary
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Consolidated Financial Year Tax Profile & Old vs New Regime Comparison
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={financialYear}
            onChange={(e) => setFinancialYear(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            {fyOptions.map((fy) => (
              <option key={fy} value={fy}>
                FY {fy}
              </option>
            ))}
          </select>

          <button
            onClick={handleExportCsv}
            disabled={isExportingCsv}
            className="inline-flex items-center rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 disabled:opacity-50"
          >
            {isExportingCsv ? '⏳ Exporting...' : '📥 CSV Export'}
          </button>

          <button
            onClick={handleExportPdf}
            disabled={isExportingPdf}
            className="inline-flex items-center rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
          >
            {isExportingPdf ? '⏳ Generating...' : '📄 PDF Report'}
          </button>
        </div>
      </div>

      {/* Prominent Legal Warning Disclaimer Banner */}
      <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 dark:border-amber-700/60 dark:bg-amber-950/30">
        <div className="flex items-start gap-3">
          <span className="text-xl">⚠️</span>
          <div className="space-y-1 text-xs text-amber-900 dark:text-amber-200">
            <h4 className="font-bold text-sm text-amber-950 dark:text-amber-100">
              IMPORTANT LEGAL NOTICE & TAX DISCLAIMER
            </h4>
            <p>
              This Tax Readiness Summary and Tax Estimation tool is provided strictly for{' '}
              <strong>INFORMATIONAL, EDUCATIONAL, AND TAX/INVESTMENT PLANNING PURPOSES ONLY.</strong>
            </p>
            <ul className="list-disc pl-4 space-y-0.5">
              <li>
                Estimated tax calculations, exemptions, and regime comparisons shown DO NOT represent actual final tax liabilities payable to the Income Tax Department.
              </li>
              <li>
                Neither the application nor its developers accept ANY RESPONSIBILITY OR LIABILITY for any calculation inaccuracies, tax penalties, interest, or financial losses.
              </li>
              <li>
                For official tax calculation and Income Tax Return (ITR) filing, users <strong>MUST consult a qualified Chartered Accountant (CA)</strong>.
              </li>
            </ul>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12 text-slate-500">
          Loading tax readiness summary...
        </div>
      ) : error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700 dark:border-red-900/50 dark:bg-red-950/20 dark:text-red-300">
          {error}
        </div>
      ) : summary ? (
        <div className="space-y-6">
          {/* Dual Regime Side-by-Side Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <RegimeComparisonCard
              title="Old Tax Regime"
              regime={summary.old_regime}
              isRecommended={summary.recommended_regime === 'OLD'}
              savings={summary.recommended_regime === 'OLD' ? summary.tax_savings : 0}
              exemptionsSummary={summary.exemptions_summary_old}
            />
            <RegimeComparisonCard
              title="New Tax Regime (Section 115BAC)"
              regime={summary.new_regime}
              isRecommended={summary.recommended_regime === 'NEW'}
              savings={summary.recommended_regime === 'NEW' ? summary.tax_savings : 0}
              exemptionsSummary={summary.exemptions_summary_new}
            />
          </div>

          {/* Income & Deductions Breakdown Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Income Breakdown Card */}
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
                Gross Income & TDS Credits
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-600 dark:text-slate-400">Gross Salary</span>
                  <span className="font-medium text-slate-900 dark:text-white">
                    {formatCurrency(summary.income_summary.gross_salary)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600 dark:text-slate-400">Business Income</span>
                  <span className="font-medium text-slate-900 dark:text-white">
                    {formatCurrency(summary.income_summary.business_income)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600 dark:text-slate-400">Dividend Income</span>
                  <span className="font-medium text-slate-900 dark:text-white">
                    {formatCurrency(summary.income_summary.dividend_income)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600 dark:text-slate-400">Other Income</span>
                  <span className="font-medium text-slate-900 dark:text-white">
                    {formatCurrency(summary.income_summary.other_income)}
                  </span>
                </div>
                <div className="flex justify-between pt-2 font-bold border-t border-slate-100 dark:border-slate-800">
                  <span className="text-slate-900 dark:text-white">Total Gross Income</span>
                  <span className="text-slate-900 dark:text-white">
                    {formatCurrency(summary.income_summary.total_gross_income)}
                  </span>
                </div>
                <div className="flex justify-between pt-1 font-semibold text-blue-600 dark:text-blue-400">
                  <span>Total TDS Credits</span>
                  <span>{formatCurrency(summary.income_summary.total_tds_credits)}</span>
                </div>
              </div>
            </div>

            {/* Chapter VI-A Deductions Card */}
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
                Chapter VI-A Deductions
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-600 dark:text-slate-400">Section 80C (Limit ₹1.5L)</span>
                  <span className="font-medium text-slate-900 dark:text-white">
                    {formatCurrency(summary.deduction_summary.section_80c)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600 dark:text-slate-400">Section 80D (Health Insurance)</span>
                  <span className="font-medium text-slate-900 dark:text-white">
                    {formatCurrency(summary.deduction_summary.section_80d)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600 dark:text-slate-400">Section 80CCD(1B) (NPS)</span>
                  <span className="font-medium text-slate-900 dark:text-white">
                    {formatCurrency(summary.deduction_summary.section_80ccd_1b)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600 dark:text-slate-400">Section 80E / 80G / 80TTA</span>
                  <span className="font-medium text-slate-900 dark:text-white">
                    {formatCurrency(
                      summary.deduction_summary.section_80e +
                        summary.deduction_summary.section_80g +
                        summary.deduction_summary.section_80tta_80ttb +
                        summary.deduction_summary.other_deductions
                    )}
                  </span>
                </div>
                <div className="flex justify-between pt-2 font-bold border-t border-slate-100 dark:border-slate-800">
                  <span className="text-slate-900 dark:text-white">Eligible Deductions</span>
                  <span className="text-emerald-600 dark:text-emerald-400">
                    {formatCurrency(summary.deduction_summary.total_chapter_via_deductions)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
