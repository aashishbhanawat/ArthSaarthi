import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { usePortfolio } from '../../hooks/usePortfolios';
import TransactionList from '../../components/Portfolio/TransactionList'; // This was unused
import AddTransactionModal from '../../components/Portfolio/AddTransactionModal';

const PortfolioDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const portfolioId = Number(id); // Using Number() is slightly more idiomatic
    const [isModalOpen, setIsModalOpen] = useState(false);

    const { data: portfolio, isLoading, isError, error } = usePortfolio(portfolioId);

    if (isLoading) return <div className="text-center p-8">Loading portfolio details...</div>;
    if (isError) return <div className="text-center p-8 text-red-500">Error: {error?.message || 'An unknown error occurred'}</div>;
    if (!portfolio) return <div className="text-center p-8">Portfolio not found.</div>;

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold">{portfolio.name}</h1>
                <div>
                    <Link to="/portfolios" className="text-blue-600 hover:underline mr-4">&larr; Back to Portfolios</Link>
                    <button onClick={() => setIsModalOpen(true)} className="btn btn-primary">Add Transaction</button>
                </div>
            </div>

            <p className="text-gray-600 mb-8">{portfolio.description}</p>

            <TransactionList transactions={portfolio.transactions || []} />

            {isModalOpen && (
                <AddTransactionModal portfolioId={portfolioId} onClose={() => setIsModalOpen(false)} />
            )}
        </div>
    );
};

export default PortfolioDetailPage;