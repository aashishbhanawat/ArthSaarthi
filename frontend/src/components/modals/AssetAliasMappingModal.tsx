import React, { useState } from 'react';
import { usePortfolioAssets } from '../../hooks/usePortfolio';
import { Asset } from '../../types/asset';

interface AssetAliasMappingModalProps {
    isOpen: boolean;
    onClose: () => void;
    unrecognizedTicker: string;
    portfolioId: string;
    onAliasCreated: (alias: { alias: string; asset_id: string }) => void;
}

const AssetAliasMappingModal: React.FC<AssetAliasMappingModalProps> = ({
    isOpen,
    onClose,
    unrecognizedTicker,
    portfolioId,
    onAliasCreated,
}) => {
    const [selectedAssetId, setSelectedAssetId] = useState<string>('');
    const { data: assets, isLoading, error } = usePortfolioAssets(portfolioId);

    const handleSave = () => {
        if (selectedAssetId) {
            onAliasCreated({
                alias: unrecognizedTicker,
                asset_id: selectedAssetId,
            });
            onClose();
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal modal-open">
            <div className="modal-box">
                <h3 className="font-bold text-lg">Map Unrecognized Ticker</h3>
                <p className="py-4">
                    The ticker symbol <span className="font-mono bg-gray-200 px-1 rounded">{unrecognizedTicker}</span> was not found in your assets.
                    Please map it to an existing asset in your portfolio.
                </p>

                <div className="form-control w-full">
                    <label className="label">
                        <span className="label-text">Select Asset</span>
                    </label>
                    <select
                        className="select select-bordered w-full"
                        value={selectedAssetId}
                        onChange={(e) => setSelectedAssetId(e.target.value)}
                        disabled={isLoading}
                    >
                        <option value="" disabled>
                            {isLoading ? 'Loading assets...' : 'Select an asset'}
                        </option>
                        {assets?.map((asset: Asset) => (
                            <option key={asset.id} value={asset.id}>
                                {asset.name} ({asset.ticker_symbol})
                            </option>
                        ))}
                    </select>
                    {error && <p className="text-red-500 text-xs mt-1">{error.message}</p>}
                </div>

                <div className="modal-action">
                    <button onClick={onClose} className="btn btn-ghost">Cancel</button>
                    <button onClick={handleSave} className="btn btn-primary" disabled={!selectedAssetId}>
                        Save Mapping
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AssetAliasMappingModal;
