import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { usePortfolio, usePortfolioAnalytics, usePortfolioSummary, usePortfolioHoldings, useDeleteTransaction, useAssetTransactions } from '../../hooks/usePortfolios';
import { useDeleteFixedDeposit } from '../../hooks/useFixedDeposits';
import { useDeleteRecurringDeposit } from '../../hooks/useRecurringDeposits';
import TransactionFormModal from '../../components/Portfolio/TransactionFormModal';
import AnalyticsCard from '../../components/Portfolio/AnalyticsCard';
import PortfolioSummary from '../../components/Portfolio/PortfolioSummary';
import HoldingsTable from '../../components/Portfolio/HoldingsTable';
import { Holding } from '../../types/holding';
import { Transaction } from '../../types/portfolio';
import HoldingDetailModal from '../../components/Portfolio/HoldingDetailModal';
import FixedDepositDetailModal from '../../components/Portfolio/FixedDepositDetailModal';
import RecurringDepositDetailModal from '../../components/Portfolio/RecurringDepositDetailModal';
import { DeleteConfirmationModal } from '../../components/common/DeleteConfirmationModal';

const PortfolioDetailPage: React.FC = () => {
    const { id: portfolioId } = useParams<{ id: string }>();

    const { data: portfolio, isLoading, isError, error } = usePortfolio(portfolioId);
    const { data: summary, isLoading: isSummaryLoading, error: summaryError } = usePortfolioSummary(portfolioId);
    const { data: holdings, isLoading: isHoldingsLoading, error: holdingsError } = usePortfolioHoldings(portfolioId);
    const { data: analytics, isLoading: isAnalyticsLoading, error: analyticsError } = usePortfolioAnalytics(portfolioId);
    const deleteTransactionMutation = useDeleteTransaction();
    const deleteFixedDepositMutation = useDeleteFixedDeposit();
    const deleteRecurringDepositMutation = useDeleteRecurringDeposit();

    const [isTransactionFormOpen, setTransactionFormOpen] = useState(false);
    const [selectedHolding, setSelectedHolding] = useState<Holding | null>(null);
    useAssetTransactions(portfolioId, selectedHolding?.asset_id, { enabled: !!selectedHolding });
    const [transactionToEdit, setTransactionToEdit] = useState<Transaction | undefined>(undefined);
    const [transactionToDelete, setTransactionToDelete] = useState<Transaction | null>(null);
    const [fdToDelete, setFdToDelete] = useState<Holding | null>(null);
    const [rdToDelete, setRdToDelete] = useState<Holding | null>(null);

    useEffect(() => {
        if (selectedHolding && holdings?.holdings) {
            const updatedHolding = holdings.holdings.find(h => h.asset_id === selectedHolding.asset_id);
            if (updatedHolding) {
                if (JSON.stringify(updatedHolding) !== JSON.stringify(selectedHolding)) {
                    setSelectedHolding(updatedHolding);
                }
            } else {
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
        if (fdToDelete && portfolioId) {
            deleteFixedDepositMutation.mutate({ portfolioId, fdId: fdToDelete.asset_id }, {
                onSuccess: () => {
                    handleCloseDetailModal();
                    setFdToDelete(null);
                }
            });
        }
        if (rdToDelete && portfolioId) {
            deleteRecurringDepositMutation.mutate({ portfolioId, rdId: rdToDelete.asset_id }, {
                onSuccess: () => {
                    handleCloseDetailModal();
                    setRdToDelete(null);
                }
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
                    <div className="flex space-x-2">
                        <Link to={`/transactions?portfolio_id=${portfolio.id}`} className="btn btn-secondary">
                            View History
                        </Link>
                        <button onClick={handleOpenCreateTransactionModal} className="btn btn-primary">Add Transaction</button>
                    </div>
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
                    isOpen={isTransactionFormOpen}
                    portfolioId={portfolio.id}
                    transactionToEdit={transactionToEdit}
                />
            )}

            {selectedHolding && !isTransactionFormOpen && !transactionToDelete && !rdToDelete && (
                <>
                    {selectedHolding.asset_type === 'FIXED_DEPOSIT' ? (
                        <FixedDepositDetailModal
                            holding={selectedHolding}
                            onClose={handleCloseDetailModal}
                            onEdit={() => {
                                handleCloseDetailModal();
                                handleOpenCreateTransactionModal();
                            }}
                            onDelete={() => setFdToDelete(selectedHolding)}
                        />
                    ) : selectedHolding.asset_type === 'RECURRING_DEPOSIT' ? (
                        <RecurringDepositDetailModal
                            holding={selectedHolding}
                            onClose={handleCloseDetailModal}
                            onEdit={() => {
                                handleCloseDetailModal();
                                handleOpenCreateTransactionModal();
                            }}
                            onDelete={() => setRdToDelete(selectedHolding)}
                        />
                    ) : (
                        <HoldingDetailModal
                            holding={selectedHolding}
                            portfolioId={portfolio.id}
                            onClose={handleCloseDetailModal}
                            onEditTransaction={handleOpenEditTransactionModal}
                            onDeleteTransaction={handleOpenDeleteModal}
                        />
                    )}
                </>
            )}

            {(transactionToDelete || fdToDelete || rdToDelete) && (
                <DeleteConfirmationModal
                    isOpen={!!transactionToDelete || !!fdToDelete || !!rdToDelete}
                    onClose={() => {
                        setTransactionToDelete(null);
                        setFdToDelete(null);
                        setRdToDelete(null);
                    }}
                    onConfirm={handleConfirmDelete}
                    title={fdToDelete ? "Delete Fixed Deposit" : rdToDelete ? "Delete Recurring Deposit" : "Delete Transaction"}
                    message={
                        fdToDelete
                            ? `Are you sure you want to delete the FD "${fdToDelete.asset_name}"? This action cannot be undone.`
                            : rdToDelete
                            ? `Are you sure you want to delete the RD "${rdToDelete.asset_name}"? This action cannot be undone.`
                            : `Are you sure you want to delete this ${transactionToDelete?.transaction_type} transaction of ${Number(transactionToDelete?.quantity).toLocaleString()} units? This action cannot be undone.`
                    }
                    isDeleting={deleteTransactionMutation.isPending || deleteFixedDepositMutation.isPending || deleteRecurringDepositMutation.isPending}
                />
            )}
        </div>
    );
};

export default PortfolioDetailPage;