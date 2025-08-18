import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { usePortfolio, usePortfolioAnalytics, usePortfolioSummary, usePortfolioHoldings, useDeleteTransaction } from '../../hooks/usePortfolios';
import TransactionFormModal from '../../components/Portfolio/TransactionFormModal';
import AnalyticsCard from '../../components/Portfolio/AnalyticsCard';
import PortfolioSummary from '../../components/Portfolio/PortfolioSummary';
import HoldingsTable from '../../components/Portfolio/HoldingsTable';
import { Holding } from '../../types/holding';
import { Transaction } from '../../types/portfolio';
import HoldingDetailModal from '../../components/Portfolio/HoldingDetailModal';
import { DeleteConfirmationModal } from '../../components/common/DeleteConfirmationModal';

const PortfolioDetailPage: React.FC = () => {
    const { id: portfolioId } = useParams<{ id: string }>();

    const { data: portfolio, isLoading, isError, error } = usePortfolio(portfolioId);
    const { data: summary, isLoading: isSummaryLoading, error: summaryError } = usePortfolioSummary(portfolioId);
    const { data: holdings, isLoading: isHoldingsLoading, error: holdingsError } = usePortfolioHoldings(portfolioId);
    const { data: analytics, isLoading: isAnalyticsLoading, error: analyticsError } = usePortfolioAnalytics(portfolioId);
    const deleteTransactionMutation = useDeleteTransaction();

    const [isTransactionFormOpen, setTransactionFormOpen] = useState(false);
    const [selectedHolding, setSelectedHolding] = useState<Holding | null>(null);
    const [transactionToEdit, setTransactionToEdit] = useState<Transaction | undefined>(undefined);
    const [transactionToDelete, setTransactionToDelete] = useState<Transaction | null>(null);

    useEffect(() => {
        // This effect syncs the selectedHolding state with the latest data from the usePortfolioHoldings hook.
        // This is crucial for updating the HoldingDetailModal in-place after a transaction is created, updated, or deleted.
        if (selectedHolding && holdings?.holdings) {
            const updatedHolding = holdings.holdings.find(h => h.asset_id === selectedHolding.asset_id);
            if (updatedHolding) {
                // Avoid unnecessary re-renders if the data hasn't changed.
                if (JSON.stringify(updatedHolding) !== JSON.stringify(selectedHolding)) {
                    setSelectedHolding(updatedHolding);
                }
            } else {
                // The holding no longer exists (e.g., all shares sold and transaction deleted), so close the modal.
                setSelectedHolding(null);
            }
        }
    }, [holdings, selectedHolding]);

    if (isLoading) return <div className="text-center p-8">Loading portfolio details...</div>;
    if (isError) return <div className="text-center p-8 text-red-500">Error: {error.message}</div>;
    if (!portfolio) return <div className="text-center p-8">Portfolio not found.</div>;

    const handleHoldingClick = (holding: Holding) => {
        setSelectedHolding(holding);
    };

    const handleCloseDetailModal = () => {
        setSelectedHolding(null);
    };

    const handleOpenCreateTransactionModal = () => {
        setTransactionToEdit(undefined);
        setTransactionFormOpen(true);
    };

    const handleOpenEditTransactionModal = (transaction: Transaction) => {
        setTransactionToEdit(transaction);
        setTransactionFormOpen(true);
    };

    const handleCloseTransactionModal = () => {
        setTransactionToEdit(undefined);
        setTransactionFormOpen(false);
    };

    const handleOpenDeleteModal = (transaction: Transaction) => {
        setTransactionToDelete(transaction);
    };

    const handleCloseDeleteModal = () => {
        setTransactionToDelete(null);
    };

    const handleConfirmDelete = () => {
        if (transactionToDelete && portfolioId) {
            deleteTransactionMutation.mutate({ portfolioId, transactionId: transactionToDelete.id }, {
                onSuccess: handleCloseDeleteModal
            });
        }
    };

    return (
        <div>
            <div className="mb-8">
                <Link to="/portfolios" className="text-blue-600 hover:underline text-sm">
                    &larr; Back to Portfolios
                </Link>
                <div className="flex justify-between items-center mt-2">
                    <h1 className="text-3xl font-bold">{portfolio.name}</h1>
                    <button onClick={handleOpenCreateTransactionModal} className="btn btn-primary">
                        Add Transaction
                    </button>
                </div>
                <p className="text-gray-600 mt-1">{portfolio.description}</p>
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
                    onClose={handleCloseTransactionModal}
                    portfolioId={portfolio.id}
                    transactionToEdit={transactionToEdit}
                />
            )}

            {/* Only show the detail modal if a holding is selected AND no other modal is active */}
            {selectedHolding && !isTransactionFormOpen && !transactionToDelete && (
                <HoldingDetailModal
                    holding={selectedHolding}
                    portfolioId={portfolio.id}
                    onClose={handleCloseDetailModal}
                    onEditTransaction={handleOpenEditTransactionModal}
                    onDeleteTransaction={handleOpenDeleteModal}
                />
            )}

            {transactionToDelete && (
                <DeleteConfirmationModal
                    isOpen={!!transactionToDelete}
                    onClose={handleCloseDeleteModal}
                    onConfirm={handleConfirmDelete}
                    title="Delete Transaction"
                    message={`Are you sure you want to delete this ${transactionToDelete.transaction_type} transaction of ${Number(transactionToDelete.quantity).toLocaleString()} units? This action cannot be undone.`}
                    isDeleting={deleteTransactionMutation.isPending}
                />
            )}
        </div>
    );
};

export default PortfolioDetailPage;