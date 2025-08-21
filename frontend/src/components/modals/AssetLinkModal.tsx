import React, { useState } from 'react';
import { usePortfolios, useAssets } from '../../hooks/usePortfolios';
import { useCreateGoalLink } from '../../hooks/useGoals';

interface AssetLinkModalProps {
  isOpen: boolean;
  onClose: () => void;
  goalId: string;
}

const AssetLinkModal: React.FC<AssetLinkModalProps> = ({ isOpen, onClose, goalId }) => {
  const { data: portfolios } = usePortfolios();
  const { data: assets } = useAssets();
  const createGoalLink = useCreateGoalLink();
  const [selectedLink, setSelectedLink] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const [type, id] = selectedLink.split('-');
    if (type === 'portfolio') {
      createGoalLink.mutate({ goalId, data: { portfolio_id: id } });
    } else {
      createGoalLink.mutate({ goalId, data: { asset_id: id } });
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center">
      <div className="bg-white p-6 rounded-lg">
        <h2 className="text-2xl font-bold mb-4">Link Asset to Goal</h2>
        <form onSubmit={handleSubmit}>
          <select
            value={selectedLink}
            onChange={(e) => setSelectedLink(e.target.value)}
            className="w-full p-2 border rounded"
          >
            <option value="">Select an asset or portfolio</option>
            {portfolios?.map((p) => (
              <option key={p.id} value={`portfolio-${p.id}`}>{p.name} (Portfolio)</option>
            ))}
            {assets?.map((a) => (
              <option key={a.id} value={`asset-${a.id}`}>{a.name}</option>
            ))}
          </select>
          <div className="mt-4 flex justify-end gap-2">
            <button type="button" onClick={onClose} className="px-4 py-2 bg-gray-300 rounded">
              Cancel
            </button>
            <button type="submit" className="px-4 py-2 bg-blue-500 text-white rounded">
              Link
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AssetLinkModal;
