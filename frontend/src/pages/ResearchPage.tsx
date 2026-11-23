import React from 'react';
import ResearchIntelligenceFeed from '../components/Dashboard/ResearchIntelligenceFeed';
import HelpLink from '../components/HelpLink';

export const ResearchPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Market & Research</h1>
            <HelpLink sectionId="market-research" />
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Real-time corporate news, broker target prices, and earnings concall insights for your portfolio holdings.
          </p>
        </div>
      </div>

      <ResearchIntelligenceFeed />
    </div>
  );
};

export default ResearchPage;
