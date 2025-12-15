import React, { useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { usePortfolios, usePortfolioAssets } from '../../hooks/usePortfolios';

const TransactionFilterBar: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  // Component's state is derived directly from URL search params for controlled inputs
  const portfolioId = searchParams.get('portfolio_id') || '';
  const assetId = searchParams.get('asset_id') || '';
  const transactionType = searchParams.get('transaction_type') || 'ALL';
  const startDate = searchParams.get('start_date') || '';
  const endDate = searchParams.get('end_date') || '';

  const { data: portfolios, isLoading: isLoadingPortfolios } = usePortfolios();
  // Only fetch assets if a portfolio is selected
  const { data: assets, isLoading: isLoadingAssets } = usePortfolioAssets(portfolioId);

  // When a filter changes, update the URL search params immediately
  const handleFilterChange = useCallback((key: string, value: string) => {
    setSearchParams((prev) => {
      if (value) {
        prev.set(key, value);
      } else {
        prev.delete(key);
      }
      // Reset to the first page whenever filters change
      prev.set('page', '0');

      // If the portfolio changes, reset the asset filter as it's no longer valid
      if (key === 'portfolio_id') {
        prev.delete('asset_id');
      }
      return prev;
    });
  }, [setSearchParams]);

  const handleReset = () => {
    setSearchParams({});
  };

  // A small UX improvement: if there's only one portfolio, select it by default.
  useEffect(() => {
    if (portfolios && portfolios.length === 1 && !portfolioId) {
      handleFilterChange('portfolio_id', portfolios[0].id);
    }
  }, [portfolios, portfolioId, handleFilterChange]);

  return (
    <div className="card bg-gray-50 p-4 mb-6">
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 items-end">
        {/* Portfolio Dropdown */}
        <div className="form-group">
          <label htmlFor="portfolio-filter" className="form-label">
            Portfolio
          </label>
          <select
            id="portfolio-filter"
            className="form-input"
            value={portfolioId}
            onChange={(e) => handleFilterChange('portfolio_id', e.target.value)}
            disabled={isLoadingPortfolios}
          >
            <option value="">-- Select a Portfolio --</option>
            {portfolios?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {/* Asset Dropdown */}
        <div className="form-group">
          <label htmlFor="asset-filter" className="form-label">Asset</label>
          <select
            id="asset-filter"
            className="form-input"
            value={assetId}
            onChange={(e) => handleFilterChange('asset_id', e.target.value)}
            disabled={!portfolioId || isLoadingAssets}
          >
            <option value="">All Assets</option>
            {assets?.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name} ({a.ticker_symbol})
              </option>
            ))}
          </select>
        </div>

        {/* Transaction Type */}
        <div className="form-group">
          <label htmlFor="type-filter" className="form-label">Type</label>
          <select id="type-filter" className="form-input" value={transactionType} onChange={(e) => handleFilterChange('transaction_type', e.target.value === 'ALL' ? '' : e.target.value)}>
            <option value="ALL">All</option>
            <option value="BUY">Buy</option>
            <option value="SELL">Sell</option>
            <option value="DIVIDEND">Dividend</option>
            <option value="SPLIT">Split</option>
            <option value="BONUS">Bonus</option>
            <option value="RSU_VEST">RSU Vest</option>
            <option value="ESPP_PURCHASE">ESPP Purchase</option>
          </select>
        </div>

        {/* Start Date & End Date */}
        <div className="form-group"><label htmlFor="start-date-filter" className="form-label">Start Date</label><input type="date" id="start-date-filter" className="form-input" value={startDate} onChange={(e) => handleFilterChange('start_date', e.target.value)} /></div>
        <div className="form-group"><label htmlFor="end-date-filter" className="form-label">End Date</label><input type="date" id="end-date-filter" className="form-input" value={endDate} onChange={(e) => handleFilterChange('end_date', e.target.value)} /></div>

        {/* Action Buttons */}
        <div className="flex space-x-2"><button type="button" onClick={handleReset} className="btn btn-secondary w-full">Reset</button></div>
      </div>
    </div>
  );
};

export default TransactionFilterBar;