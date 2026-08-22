import React from 'react';
import { EyeIcon, PlusIcon } from '@heroicons/react/24/outline';

interface WatchlistEmptyStateProps {
  onCreateClick?: () => void;
}

export const WatchlistEmptyState: React.FC<WatchlistEmptyStateProps> = ({ onCreateClick }) => {
  return (
    <div className="text-center py-16 px-4">
      <EyeIcon className="mx-auto h-12 w-12 text-gray-400" aria-hidden="true" />
      <h3 className="mt-2 text-lg font-medium text-gray-900 dark:text-white">No watchlist selected</h3>
      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Select a watchlist from the side panel to view its assets, or create a new one to get started.
      </p>
      {onCreateClick && (
        <div className="mt-6 flex justify-center">
          <button
            type="button"
            onClick={onCreateClick}
            className="btn btn-primary inline-flex items-center gap-2"
          >
            <PlusIcon className="h-5 w-5" aria-hidden="true" />
            Create Watchlist
          </button>
        </div>
      )}
    </div>
  );
};