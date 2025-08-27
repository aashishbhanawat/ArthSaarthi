import React, { useState } from 'react';
import { usePortfolios } from '../../hooks/usePortfolios';
import { useAssetSearch } from '../../hooks/useAssets';
import { Goal } from '../../types/goal';
import { Portfolio } from '../../types/portfolio';
import { Asset } from '../../types/asset';

interface AssetLinkModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLink: (link: { portfolio_id?: string; asset_id?: string }) => void;
  goal: Goal;
}

const AssetLinkModal: React.FC<AssetLinkModalProps> = ({ isOpen, onClose, onLink, goal }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const { data: portfolios, isLoading: isLoadingPortfolios } = usePortfolios();
  const { data: assets, isLoading: isLoadingAssets } = useAssetSearch(searchTerm);

  const handleLink = (link: { portfolio_id?: string; asset_id?: string }) => {
    onLink(link);
    onClose();
  };

  if (!isOpen) return null;

  const alreadyLinked = (type: 'asset' | 'portfolio', id: string): boolean => {
    if (!goal?.links) return false;
    if (type === 'asset') {
        return goal.links.some(link => link.asset_id === id);
    }
    return goal.links.some(link => link.portfolio_id === id);
  }

  const renderPortfolios = () => (
    <div>
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Portfolios</h3>
        {isLoadingPortfolios ? <p>Loading...</p> : (
            <div className="space-y-2">
                {portfolios?.map((portfolio: Portfolio) => (
                    <div key={portfolio.id} className="flex justify-between items-center bg-gray-50 p-3 rounded-lg">
                        <p className="font-semibold">{portfolio.name}</p>
                        <button onClick={() => handleLink({ portfolio_id: portfolio.id })} className="btn btn-sm btn-secondary" disabled={alreadyLinked('portfolio', portfolio.id)}>
                            {alreadyLinked('portfolio', portfolio.id) ? 'Linked' : 'Link Portfolio'}
                        </button>
                    </div>
                ))}
            </div>
        )}
    </div>
  );

  const renderAssets = () => (
    <div>
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Assets</h3>
        {isLoadingAssets ? <p>Searching...</p> : (
            <div className="space-y-2">
                {assets?.map((asset: Asset) => (
                     <div key={asset.id} className="flex justify-between items-center bg-gray-50 p-3 rounded-lg">
                        <div>
                            <p className="font-semibold">{asset.name}</p>
                            <p className="text-sm text-gray-500">{asset.ticker_symbol}</p>
                        </div>
                        <button onClick={() => handleLink({ asset_id: asset.id })} className="btn btn-sm btn-secondary" disabled={alreadyLinked('asset', asset.id)}>
                             {alreadyLinked('asset', asset.id) ? 'Linked' : 'Link Asset'}
                        </button>
                    </div>
                ))}
            </div>
        )}
    </div>
  );


  return (
    <div className="modal-overlay">
        <div className="modal-content max-w-lg">
            <div className="modal-header">
                <h2 className="text-2xl font-bold">Link Asset or Portfolio to "{goal.name}"</h2>
                <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
            </div>
            <div className="p-6">
                <div className="form-group">
                    <label htmlFor="asset-search" className="form-label">
                        Search Assets
                    </label>
                    <input
                        id="asset-search"
                        type="text"
                        placeholder="Search for an asset..."
                        className="form-input"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="mt-6">
                    {searchTerm ? renderAssets() : renderPortfolios()}
                </div>
                <div className="flex items-center justify-end pt-6 border-t mt-6">
                    <button type="button" onClick={onClose} className="btn btn-secondary">
                        Close
                    </button>
                </div>
            </div>
        </div>
    </div>
  );
};

export default AssetLinkModal;
