import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Portfolio } from '../../types/portfolio';
import { TrashIcon } from '@heroicons/react/24/outline';
import { useDeletePortfolio } from '../../hooks/usePortfolios';
import DeletePortfolioModal from './DeletePortfolioModal';

interface PortfolioListProps {
    portfolios: Portfolio[];
}

const PortfolioList: React.FC<PortfolioListProps> = ({ portfolios }) => {
    const [isModalOpen, setModalOpen] = useState(false);
    const [portfolioToDelete, setPortfolioToDelete] = useState<Portfolio | null>(null);
    const deletePortfolioMutation = useDeletePortfolio();

    const handleDeleteClick = (portfolio: Portfolio) => {
        setPortfolioToDelete(portfolio);
        setModalOpen(true);
    };

    const handleConfirmDelete = () => {
        if (portfolioToDelete) {
            deletePortfolioMutation.mutate(portfolioToDelete.id, {
                onSuccess: () => setModalOpen(false),
            });
        }
    };

    if (portfolios.length === 0) {
        return <p className="text-center text-gray-500 dark:text-gray-400 mt-8">You don't have any portfolios yet. Create one to get started!</p>;
    }

    return (
        <>
            <div className="space-y-4">
                {portfolios.map((portfolio) => (
                    <div key={portfolio.id} className="card flex justify-between items-center">
                        <Link to={`/portfolios/${portfolio.id}`} className="text-xl font-semibold text-blue-600 hover:underline dark:text-blue-400">
                            {portfolio.name}
                        </Link>
                        <button
                            onClick={() => handleDeleteClick(portfolio)}
                            className="btn btn-sm btn-ghost text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/30"
                            disabled={deletePortfolioMutation.isPending}
                            aria-label={`Delete portfolio ${portfolio.name}`}>
                            <TrashIcon className="h-5 w-5" />
                        </button>
                    </div>
                ))}
            </div>
            <DeletePortfolioModal
                isOpen={isModalOpen}
                onClose={() => setModalOpen(false)}
                onConfirm={handleConfirmDelete}
                portfolioName={portfolioToDelete?.name || ''}
                isPending={deletePortfolioMutation.isPending}
            />
        </>
    );
};

export default PortfolioList;