import React, { useState } from 'react';
import { useCapitalSetOff } from '../../hooks/useCapitalGains';
import { CapitalLossLedgerModal } from './CapitalLossLedgerModal';

interface CapitalGainsNetSummaryCardProps {
  fy: string;
  portfolioId?: string;
  slabRate: number;
  isPrivacyMode?: boolean;
}

export const CapitalGainsNetSummaryCard: React.FC<CapitalGainsNetSummaryCardProps> = ({
  fy,
  portfolioId,
  slabRate,
  isPrivacyMode = false,
}) => {
  const [isLedgerModalOpen, setIsLedgerModalOpen] = useState(false);
  const { data: setOffData, isLoading } = useCapitalSetOff({
    fy,
    portfolio_id: portfolioId,
    slab_rate: slabRate,
  });

  const maskValue = (val: number | string) => {
    if (isPrivacyMode) return '••••••';
    const num = typeof val === 'string' ? parseFloat(val) : val;
    return `₹${(num || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const parseNum = (val: number | string) => (typeof val === 'string' ? parseFloat(val) : val) || 0;

  if (isLoading || !setOffData) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg animate-pulse">
        <div className="h-5 bg-slate-800 rounded w-1/3 mb-4"></div>
        <div className="h-20 bg-slate-800/50 rounded mb-4"></div>
      </div>
    );
  }

  const { breakdown } = setOffData;

  return (
    <>
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg text-slate-100">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-100">Net Taxable Capital Gains Summary</h2>
              <span className="text-xs px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 font-semibold">
                Sec 70/71/74 Set-Off Engine
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Assessment Year {setOffData.assessment_year} • Slab Rate {slabRate}%
            </p>
          </div>

          <button
            onClick={() => setIsLedgerModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg transition"
          >
            <span>📋 Loss Ledger ({setOffData.loss_ledger_entries.length})</span>
          </button>
        </div>

        {/* Set-off Metric Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 my-4">
          <div className="bg-slate-950/70 p-3.5 rounded-lg border border-slate-800">
            <span className="text-[11px] text-slate-400 uppercase font-medium">Gross Realized STCG / STCL</span>
            <div className="text-sm font-semibold mt-1 font-mono">
              <span className="text-emerald-400">{maskValue(breakdown.gross_stcg)}</span>
              {' / '}
              <span className="text-rose-400">{maskValue(breakdown.gross_stcl)}</span>
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Before intra-head set-off</div>
          </div>

          <div className="bg-slate-950/70 p-3.5 rounded-lg border border-slate-800">
            <span className="text-[11px] text-slate-400 uppercase font-medium">Gross Realized LTCG / LTCL</span>
            <div className="text-sm font-semibold mt-1 font-mono">
              <span className="text-emerald-400">{maskValue(breakdown.gross_ltcg)}</span>
              {' / '}
              <span className="text-rose-400">{maskValue(breakdown.gross_ltcl)}</span>
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Before intra-head set-off</div>
          </div>

          <div className="bg-slate-950/70 p-3.5 rounded-lg border border-slate-800">
            <span className="text-[11px] text-slate-400 uppercase font-medium">Net Taxable STCG</span>
            <div className="text-base font-bold text-emerald-400 mt-1 font-mono">
              {maskValue(breakdown.net_taxable_stcg)}
            </div>
            <div className="text-[10px] text-slate-400 mt-1">
              After CY & BF Set-off
            </div>
          </div>

          <div className="bg-slate-950/70 p-3.5 rounded-lg border border-slate-800">
            <span className="text-[11px] text-slate-400 uppercase font-medium">Net Taxable LTCG</span>
            <div className="text-base font-bold text-emerald-400 mt-1 font-mono">
              {maskValue(breakdown.net_taxable_ltcg)}
            </div>
            <div className="text-[10px] text-slate-400 mt-1">
              After CY & BF Set-off
            </div>
          </div>
        </div>

        {/* Set-off Breakdown & Tax Savings Banner */}
        <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="text-xs space-y-1">
            <div className="text-slate-300 font-semibold">Statutory Set-off Applied:</div>
            <div className="text-slate-400">
              • Current Year STCL Offset: <span className="text-slate-200 font-mono">{maskValue(parseNum(breakdown.cy_stcl_offset_against_stcg) + parseNum(breakdown.cy_stcl_offset_against_ltcg))}</span>
              {' | '} LTCL Offset: <span className="text-slate-200 font-mono">{maskValue(breakdown.cy_ltcl_offset_against_ltcg)}</span>
            </div>
            <div className="text-slate-400">
              • Brought-Forward Loss Used: STCL <span className="text-slate-200 font-mono">{maskValue(breakdown.bf_stcl_used)}</span>
              {' | '} LTCL <span className="text-slate-200 font-mono">{maskValue(breakdown.bf_ltcl_used)}</span>
            </div>
          </div>

          <div className="text-right">
            <div className="text-xs text-slate-400">Tax Saved via Set-Off</div>
            <div className="text-lg font-bold text-cyan-400 font-mono">
              {maskValue(breakdown.tax_saved_via_setoff)}
            </div>
            <div className="text-[10px] text-emerald-400 font-medium">
              Net Estimated Tax: {maskValue(breakdown.net_estimated_tax)}
            </div>
          </div>
        </div>
      </div>


      <CapitalLossLedgerModal
        isOpen={isLedgerModalOpen}
        onClose={() => setIsLedgerModalOpen(false)}
        currentFy={fy}
      />
    </>
  );
};
