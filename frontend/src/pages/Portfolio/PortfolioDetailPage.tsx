import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { usePortfolio, usePortfolioAnalytics, usePortfolioSummary, usePortfolioHoldings } from '../../hooks/usePortfolios';
import TransactionFormModal from '../../components/Portfolio/TransactionFormModal';
import AnalyticsCard from '../../components/Portfolio/AnalyticsCard';
import PortfolioSummary from '../../components/Portfolio/PortfolioSummary';
import HoldingsTable from '../../components/Portfolio/HoldingsTable';
import { Holding } from '../../types/holding';
import HoldingDetailModal from '../../components/Portfolio/HoldingDetailModal';

const PortfolioDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();

    const { data: portfolio, isLoading, isError, error } = usePortfolio(id);
    const { data: summary, isLoading: isSummaryLoading, error: summaryError } = usePortfolioSummary(id);
    const { data: holdings, isLoading: isHoldingsLoading, error: holdingsError } = usePortfolioHoldings(id);
    const { data: analytics, isLoading: isAnalyticsLoading, error: analyticsError } = usePortfolioAnalytics(id);

    const [isTransactionFormOpen, setTransactionFormOpen] = useState(false);
    const [selectedHolding, setSelectedHolding] = useState<Holding | null>(null);

    if (isLoading) return <div className="text-center p-8">Loading portfolio details...</div>;
    if (isError) return <div className="text-center p-8 text-red-500">Error: {error.message}</div>;
    if (!portfolio) return <div className="text-center p-8">Portfolio not found.</div>;

    const handleHoldingClick = (holding: Holding) => {
        setSelectedHolding(holding);
    };

    const handleCloseDetailModal = () => {
        setSelectedHolding(null);
    };

    return (
        <div>
            <div className="mb-8">
                <Link to="/portfolios" className="text-blue-600 hover:underline text-sm">
                    &larr; Back to Portfolios
                </Link>
                <div className="flex justify-between items-center mt-2">
                    <h1 className="text-3xl font-bold">{portfolio.name}</h1>
                    <button onClick={() => setTransactionFormOpen(true)} className="btn btn-primary">
                        Add Transaction
                    </button>
                </div>
            </div>

            <PortfolioSummary summary={summary} isLoading={isSummaryLoading} error={summaryError} />

            <AnalyticsCard analytics={analytics} isLoading={isAnalyticsLoading} error={analyticsError} />

            <div className="mt-8">
                <HoldingsTable
                    holdings={holdings?.holdings}
                    isLoading={isHoldingsLoading}
                    error={holdingsError}
                    onRowClick={handleHoldingClick}
                />
            </div>

            {isTransactionFormOpen && (
                <TransactionFormModal
                    onClose={() => setTransactionFormOpen(false)}
                    portfolioId={portfolio.id}
                    transactionToEdit={undefined} // Edit functionality will be handled elsewhere
                />
            )}

            {selectedHolding && (
                <HoldingDetailModal
                    holding={selectedHolding}
                    portfolioId={portfolio.id}
                    onClose={handleCloseDetailModal}
                />
            )}
        </div>
    );
};

export default PortfolioDetailPage;