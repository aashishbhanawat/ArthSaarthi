import React, { useState, useEffect } from 'react';
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
  const [inputValue, setInputValue] = useState('');
  const [searchTerm, setSearchTerm] = useState(''); // Debounced
  const { data: portfolios, isLoading: isLoadingPortfolios } = usePortfolios();
  const { data: assets, isLoading: isLoadingAssets } = useAssetSearch(searchTerm);

  // Debounce search term
  useEffect(() => {
    const handler = setTimeout(() => {
        setSearchTerm(inputValue);
    }, 300);

    return () => {
        clearTimeout(handler);
    };
  }, [inputValue]);

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

  const showPortfolios = inputValue.length === 0;

  return (
    <div className="modal-overlay">
        <div className="modal-content max-w-lg overflow-visible">
            <div className="modal-header">
                <h2 className="text-2xl font-bold">Link Item to "{goal.name}"</h2>
                <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
            </div>
            <div className="p-6">
                <div className="form-group relative">
                    <label htmlFor="asset-search" className="form-label">
                        Search Assets or Select a Portfolio
                    </label>
                    <input
                        id="asset-search"
                        type="text"
                        placeholder="Start typing to search for assets..."
                        className="form-input"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        autoComplete="off"
                    />
                    {/* Dropdown List */}
                    <div className="absolute z-20 w-full bg-white border border-gray-300 rounded-md mt-1 max-h-60 overflow-y-auto shadow-lg">
                        {showPortfolios && (
                            <ul>
                                <li className="p-2 text-sm font-semibold text-gray-500">Portfolios</li>
                                {isLoadingPortfolios ? <li className="p-2">Loading...</li> :
                                portfolios?.map((portfolio: Portfolio) => (
                                    <li key={portfolio.id} className="flex justify-between items-center p-2 hover:bg-gray-100">
                                        <span>{portfolio.name}</span>
                                        <button onClick={() => handleLink({ portfolio_id: portfolio.id })} className="btn btn-sm btn-secondary" disabled={alreadyLinked('portfolio', portfolio.id)}>
                                            {alreadyLinked('portfolio', portfolio.id) ? 'Linked' : 'Link'}
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        )}
                        {!showPortfolios && (
                            <ul>
                                <li className="p-2 text-sm font-semibold text-gray-500">Assets</li>
                                {isLoadingAssets ? <li className="p-2">Searching...</li> :
                                assets?.map((asset: Asset) => (
                                    <li key={asset.id} className="flex justify-between items-center p-2 hover:bg-gray-100">
                                        <div>
                                            <p>{asset.name}</p>
                                            <p className="text-sm text-gray-500">{asset.ticker_symbol}</p>
                                        </div>
                                        <button onClick={() => handleLink({ asset_id: asset.id })} className="btn btn-sm btn-secondary" disabled={alreadyLinked('asset', asset.id)}>
                                            {alreadyLinked('asset', asset.id) ? 'Linked' : 'Link'}
                                        </button>
                                    </li>
                                ))}
                                {!isLoadingAssets && assets?.length === 0 && <li className="p-2 text-gray-500">No assets found.</li>}
                            </ul>
                        )}
                    </div>
                </div>

                <div className="flex items-center justify-end pt-4 mt-72"> {/* mt-72 is a hack to push button below dropdown */}
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
