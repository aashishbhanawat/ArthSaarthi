import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { usePortfolio } from '../../hooks/usePortfolios';
import TransactionList from '../../components/Portfolio/TransactionList';
import AddTransactionModal from '../../components/Portfolio/AddTransactionModal';

const PortfolioDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const portfolioId = parseInt(id || '0', 10);

    const { data: portfolio, isLoading, isError, error } = usePortfolio(portfolioId);
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

            <TransactionList transactions={portfolio.transactions || []} />

            <AddTransactionModal
                isOpen={isModalOpen}
                onClose={() => setModalOpen(false)}
                portfolioId={portfolioId}
            />
        </div>
    );
};

export default PortfolioDetailPage;