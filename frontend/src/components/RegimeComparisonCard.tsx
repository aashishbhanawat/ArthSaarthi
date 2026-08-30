import React from 'react';
import { RegimeCalculation } from '../types/tax_summary';
import { formatCurrency } from '../utils/formatting';

interface RegimeComparisonCardProps {
  title: string;
  regime: RegimeCalculation;
  isRecommended: boolean;
  savings?: number;
}

export const RegimeComparisonCard: React.FC<RegimeComparisonCardProps> = ({
  title,
  regime,
  isRecommended,
  savings = 0,
}) => {
  return (
    <div
      className={`rounded-xl border p-6 shadow-sm transition-all ${
        isRecommended
          ? 'border-emerald-500 bg-emerald-50/30 dark:bg-emerald-950/20 dark:border-emerald-600 ring-2 ring-emerald-500/20'
          : 'border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900'
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">
            {title}
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {regime.regime_type === 'NEW'
              ? 'Section 115BAC Slabs (No Chapter VI-A)'
              : 'Traditional Slabs with Chapter VI-A Deductions'}
          </p>
        </div>
        {isRecommended && (
          <span className="inline-flex items-center rounded-full bg-emerald-100 dark:bg-emerald-900/60 px-3 py-1 text-xs font-semibold text-emerald-800 dark:text-emerald-300">
            ★ Recommended ({formatCurrency(savings)} Savings)
          </span>
        )}
      </div>

      <div className="space-y-3 divide-y divide-slate-100 dark:divide-slate-800 text-sm">
        <div className="flex justify-between pt-2">
          <span className="text-slate-600 dark:text-slate-400">Gross Income</span>
          <span className="font-medium text-slate-900 dark:text-white">
            {formatCurrency(regime.gross_income)}
          </span>
        </div>

        <div className="flex justify-between pt-2">
          <span className="text-slate-600 dark:text-slate-400">
            Standard Deduction / Exemptions
          </span>
          <span className="font-medium text-emerald-600 dark:text-emerald-400">
            - {formatCurrency(regime.exemptions)}
          </span>
        </div>

        <div className="flex justify-between pt-2">
          <span className="text-slate-600 dark:text-slate-400">
            Chapter VI-A Deductions
          </span>
          <span className="font-medium text-emerald-600 dark:text-emerald-400">
            - {formatCurrency(regime.chapter_via_deductions)}
          </span>
        </div>

        <div className="flex justify-between pt-2 font-semibold">
          <span className="text-slate-900 dark:text-white">Taxable Income</span>
          <span className="text-slate-900 dark:text-white">
            {formatCurrency(regime.taxable_income)}
          </span>
        </div>

        <div className="flex justify-between pt-2">
          <span className="text-slate-600 dark:text-slate-400">Tax on Income Slabs</span>
          <span className="font-medium text-slate-900 dark:text-white">
            {formatCurrency(regime.tax_on_slabs)}
          </span>
        </div>

        {regime.section_87a_rebate > 0 && (
          <div className="flex justify-between pt-2">
            <span className="text-slate-600 dark:text-slate-400">
              Section 87A Rebate
            </span>
            <span className="font-medium text-emerald-600 dark:text-emerald-400">
              - {formatCurrency(regime.section_87a_rebate)}
            </span>
          </div>
        )}

        <div className="flex justify-between pt-2">
          <span className="text-slate-600 dark:text-slate-400">
            Health & Education Cess (4%)
          </span>
          <span className="font-medium text-slate-900 dark:text-white">
            {formatCurrency(regime.cess)}
          </span>
        </div>

        <div className="flex justify-between pt-2 font-bold text-base">
          <span className="text-slate-900 dark:text-white">Total Tax Liability</span>
          <span className="text-slate-900 dark:text-white">
            {formatCurrency(regime.total_tax_liability)}
          </span>
        </div>

        <div className="flex justify-between pt-2">
          <span className="text-slate-600 dark:text-slate-400">Less: TDS Credits</span>
          <span className="font-medium text-blue-600 dark:text-blue-400">
            - {formatCurrency(regime.tds_credits)}
          </span>
        </div>

        <div className="flex justify-between pt-2 font-bold text-base border-t-2 border-slate-200 dark:border-slate-700">
          <span className="text-slate-900 dark:text-white">Net Tax Payable</span>
          <span
            className={
              regime.net_tax_payable <= 0
                ? 'text-emerald-600 dark:text-emerald-400'
                : 'text-amber-600 dark:text-amber-400'
            }
          >
            {formatCurrency(regime.net_tax_payable)}
          </span>
        </div>
      </div>
    </div>
  );
};
