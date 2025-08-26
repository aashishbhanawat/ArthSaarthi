import React from 'react';
import { EyeIcon } from '@heroicons/react/24/outline';

export const WatchlistEmptyState: React.FC = () => {
  return (
    <div className="text-center py-16 px-4">
      <EyeIcon className="mx-auto h-12 w-12 text-gray-400" />
      <h3 className="mt-2 text-lg font-medium text-gray-900 dark:text-white">No watchlist selected</h3>
      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Select a watchlist from the side panel to view its assets, or create a new one to get started.
      </p>
    </div>
  );
};