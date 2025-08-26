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
  const { data: portfolios } = usePortfolios();
  const { data: assets } = useAssetSearch(searchTerm);

  const handleLink = (link: { portfolio_id?: string; asset_id?: string }) => {
    onLink(link);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal modal-open">
      <div className="modal-box">
        <h3 className="font-bold text-lg">Link Asset or Portfolio to "{goal.name}"</h3>
        <div className="form-control w-full py-4">
          <input
            type="text"
            placeholder="Search for an asset..."
            className="input input-bordered w-full"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="grid grid-cols-1 gap-4">
          {searchTerm ? (
            assets?.map((asset: Asset) => (
              <div key={asset.id} className="card bg-base-200 shadow-md">
                <div className="card-body">
                  <h4 className="card-title">{asset.name}</h4>
                  <p>{asset.ticker_symbol}</p>
                  <div className="card-actions justify-end">
                    <button onClick={() => handleLink({ asset_id: asset.id })} className="btn btn-sm btn-primary">
                      Link Asset
                    </button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            portfolios?.map((portfolio: Portfolio) => (
              <div key={portfolio.id} className="card bg-base-200 shadow-md">
                <div className="card-body">
                  <h4 className="card-title">{portfolio.name}</h4>
                  <div className="card-actions justify-end">
                    <button onClick={() => handleLink({ portfolio_id: portfolio.id })} className="btn btn-sm btn-primary">
                      Link Portfolio
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
        <div className="modal-action mt-4">
          <button type="button" onClick={onClose} className="btn btn-ghost">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default AssetLinkModal;
