import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { usePortfolio, usePortfolioAnalytics } from '../../hooks/usePortfolios';
import TransactionList from '../../components/Portfolio/TransactionList';
import AddTransactionModal from '../../components/Portfolio/AddTransactionModal';
import AnalyticsCard from '../../components/Portfolio/AnalyticsCard';

const PortfolioDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();

    const { data: portfolio, isLoading, isError, error } = usePortfolio(id);
    const { data: analytics, isLoading: isAnalyticsLoading, error: analyticsError } = usePortfolioAnalytics(id);
    const [isModalOpen, setModalOpen] = useState(false);

    if (isLoading) return <div className="text-center p-8">Loading portfolio details...</div>;
    if (isError) return <div className="text-center p-8 text-red-500">Error: {error.message}</div>;
    if (!portfolio) return <div className="text-center p-8">Portfolio not found.</div>;

    return (
        <div>
            <div className="mb-8">
                <Link to="/portfolios" className="text-blue-600 hover:underline text-sm">
                    &larr; Back to Portfolios
                </Link>
                <div className="flex justify-between items-center mt-2">
                    <h1 className="text-3xl font-bold">{portfolio.name}</h1>
                    <button onClick={() => setModalOpen(true)} className="btn btn-primary">
                        Add Transaction
                    </button>
                </div>
            </div>

            <AnalyticsCard analytics={analytics} isLoading={isAnalyticsLoading} error={analyticsError} />

            <div className="mt-8">
                <TransactionList transactions={portfolio.transactions || []} />
            </div>

            {isModalOpen && (
                <AddTransactionModal
                    onClose={() => setModalOpen(false)}
                    portfolioId={portfolio.id}
                />
            )}
        </div>
    );
};

export default PortfolioDetailPage;