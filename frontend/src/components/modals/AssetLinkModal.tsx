import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { usePortfolios, usePortfolioAssets } from '../../hooks/usePortfolios';
import { useCreateGoalLink } from '../../hooks/useGoals';
import { Portfolio } from '../../types/portfolio';
import { Asset } from '../../types/asset';
import { GoalLinkCreateIn } from '../../types/goal';

interface AssetLinkModalProps {
  isOpen: boolean;
  onClose: () => void;
  goalId: string;
}

const AssetLinkModal: React.FC<AssetLinkModalProps> = ({ isOpen, onClose, goalId }) => {
  const [selectionType, setSelectionType] = useState<'portfolio' | 'asset'>('portfolio');
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);

  const { data: portfolios, isLoading: isLoadingPortfolios } = usePortfolios();
  const { data: assets, isLoading: isLoadingAssets } = usePortfolioAssets(selectedPortfolio?.id);

  const queryClient = useQueryClient();
  const createGoalLinkMutation = useCreateGoalLink();

  const handleLink = () => {
    let linkData: GoalLinkCreateIn = {};
    if (selectionType === 'portfolio' && selectedPortfolio) {
      linkData = { portfolio_id: selectedPortfolio.id };
    } else if (selectionType === 'asset' && selectedAsset) {
      linkData = { asset_id: selectedAsset.id };
    }

    createGoalLinkMutation.mutate({ goalId, data: linkData }, {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['goals'] });
        queryClient.invalidateQueries({ queryKey: ['goal', goalId] });
        onClose();
      },
    });
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content max-w-2xl">
        <div className="modal-header">
          <h2 className="text-2xl font-bold">Link Asset or Portfolio to Goal</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
        </div>
        <div className="p-6">
          <div className="tabs">
            <button className={`tab tab-bordered ${selectionType === 'portfolio' ? 'tab-active' : ''}`} onClick={() => setSelectionType('portfolio')}>Portfolios</button>
            <button className={`tab tab-bordered ${selectionType === 'asset' ? 'tab-active' : ''}`} onClick={() => setSelectionType('asset')}>Assets</button>
          </div>

          <div className="mt-4">
            {selectionType === 'portfolio' && (
              <div>
                <h3 className="font-bold">Select a Portfolio</h3>
                {isLoadingPortfolios ? <p>Loading portfolios...</p> : (
                  <ul className="menu bg-base-100 w-full rounded-box mt-2 border max-h-60 overflow-y-auto">
                    {portfolios?.map(p => (
                      <li key={p.id} onClick={() => setSelectedPortfolio(p)} className={selectedPortfolio?.id === p.id ? 'bordered' : ''}>
                        <a>{p.name}</a>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {selectionType === 'asset' && (
              <div>
                <h3 className="font-bold">Select a Portfolio to view its Assets</h3>
                {isLoadingPortfolios ? <p>Loading portfolios...</p> : (
                  <select className="select select-bordered w-full mb-4" onChange={e => setSelectedPortfolio(portfolios?.find(p => p.id === e.target.value) || null)}>
                      <option value="">Select a portfolio</option>
                      {portfolios?.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                )}

                {selectedPortfolio && (
                  <div>
                    <h3 className="font-bold">Select an Asset</h3>
                    {isLoadingAssets ? <p>Loading assets...</p> : (
                      <ul className="menu bg-base-100 w-full rounded-box mt-2 border max-h-60 overflow-y-auto">
                        {assets?.map(a => (
                          <li key={a.id} onClick={() => setSelectedAsset(a)} className={selectedAsset?.id === a.id ? 'bordered' : ''}>
                            <a>{a.name} ({a.ticker_symbol})</a>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="modal-action">
            <button onClick={onClose} className="btn btn-ghost">Cancel</button>
            <button onClick={handleLink} className="btn btn-primary" disabled={(!selectedPortfolio && !selectedAsset) || createGoalLinkMutation.isPending}>
              {createGoalLinkMutation.isPending ? 'Linking...' : 'Link'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssetLinkModal;
