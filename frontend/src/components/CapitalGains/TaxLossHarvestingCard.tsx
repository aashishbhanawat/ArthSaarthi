import React from 'react';
import { useTaxLossHarvesting } from '../../hooks/useCapitalGains';

interface TaxLossHarvestingCardProps {
  fy: string;
  portfolioId?: string;
  slabRate: number;
  isPrivacyMode?: boolean;
}

export const TaxLossHarvestingCard: React.FC<TaxLossHarvestingCardProps> = ({
  fy,
  portfolioId,
  slabRate,
  isPrivacyMode = false,
}) => {
  const { data: harvestingData, isLoading } = useTaxLossHarvesting({

    fy,
    portfolio_id: portfolioId,
    slab_rate: slabRate,
  });

  const maskValue = (val: number) => (isPrivacyMode ? '••••••' : `₹${val.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`);

  if (isLoading || !harvestingData) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg animate-pulse">
        <div className="h-5 bg-slate-800 rounded w-1/3 mb-4"></div>
        <div className="h-20 bg-slate-800/50 rounded mb-4"></div>
      </div>
    );
  }

  const { harvesting_opportunities, total_potential_tax_savings, total_harvestable_stcl, total_harvestable_ltcl } = harvestingData;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg text-slate-100 mt-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <span>🌾 Tax-Loss Harvesting Opportunities</span>
            </h2>
            <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-semibold">
              Actionable Recommendations
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Sell open position lots with unrealized losses before FY end to set off against realized capital gains.
          </p>
        </div>

        <div className="text-right">
          <div className="text-xs text-slate-400">Total Potential Tax Savings</div>
          <div className="text-xl font-extrabold text-emerald-400 font-mono">
            {maskValue(total_potential_tax_savings)}
          </div>
        </div>
      </div>

      {/* Summary Header */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
        <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800 flex justify-between items-center">
          <span className="text-xs text-slate-400">Harvestable STCL Opportunities:</span>
          <span className="text-sm font-bold text-rose-400 font-mono">{maskValue(total_harvestable_stcl)}</span>
        </div>
        <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800 flex justify-between items-center">
          <span className="text-xs text-slate-400">Harvestable LTCL Opportunities:</span>
          <span className="text-sm font-bold text-rose-400 font-mono">{maskValue(total_harvestable_ltcl)}</span>
        </div>
      </div>

      {/* Opportunities List */}
      {harvesting_opportunities.length === 0 ? (
        <div className="text-center py-6 bg-slate-950/50 rounded-lg border border-slate-800/80 text-slate-400 text-sm">
          🎉 No open loss positions available for harvesting in this portfolio. All open positions have positive unrealized gains!
        </div>
      ) : (
        <div className="overflow-x-auto border border-slate-800 rounded-lg">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="p-3">Asset</th>
                <th className="p-3">Loss Type</th>
                <th className="p-3 text-right">Quantity</th>
                <th className="p-3 text-right">Unrealized Loss</th>
                <th className="p-3 text-right">Potential Tax Saved</th>
                <th className="p-3">Recommendation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {harvesting_opportunities.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-800/50">
                  <td className="p-3 font-semibold text-slate-200">
                    <div>{item.asset_ticker}</div>
                    <div className="text-[10px] text-slate-400">{item.asset_name}</div>
                  </td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                        item.loss_type === 'STCL'
                          ? 'bg-rose-950 text-rose-400 border-rose-800'
                          : 'bg-amber-950 text-amber-400 border-amber-800'
                      }`}
                    >
                      {item.loss_type}
                    </span>
                  </td>
                  <td className="p-3 text-right font-mono text-slate-300">
                    {isPrivacyMode ? '••••' : item.quantity}
                  </td>
                  <td className="p-3 text-right font-mono text-rose-400 font-semibold">
                    -{maskValue(item.unrealized_loss)}
                  </td>
                  <td className="p-3 text-right font-mono text-emerald-400 font-bold">
                    {maskValue(item.potential_tax_saved)}
                  </td>
                  <td className="p-3 text-slate-300 max-w-xs truncate" title={item.recommendation_reason}>
                    {item.recommendation_reason}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
