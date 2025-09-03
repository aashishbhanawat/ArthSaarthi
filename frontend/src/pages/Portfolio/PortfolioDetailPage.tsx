import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { usePortfolio, usePortfolioAnalytics, usePortfolioSummary, usePortfolioHoldings, useDeleteTransaction } from '../../hooks/usePortfolios';
import TransactionFormModal from '../../components/Portfolio/TransactionFormModal';
import AddFixedDepositModal from '../../components/Portfolio/AddFixedDepositModal';
import AddBondModal from '../../components/Portfolio/AddBondModal';
import AddPPFAccountModal from '../../components/Portfolio/AddPPFAccountModal';
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
    const [isAddFixedDepositModalOpen, setAddFixedDepositModalOpen] = useState(false);
    const [isAddBondModalOpen, setAddBondModalOpen] = useState(false);
    const [isAddPpfModalOpen, setAddPpfModalOpen] = useState(false);
    const [selectedHolding, setSelectedHolding] = useState<Holding | null>(null);
    const [transactionToEdit, setTransactionToEdit] = useState<Transaction | undefined>(undefined);
    const [transactionToDelete, setTransactionToDelete] = useState<Transaction | null>(null);
    const [isFixedIncomeMenuOpen, setFixedIncomeMenuOpen] = useState(false);

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

    const handleOpenFixedIncomeMenu = () => {
        setFixedIncomeMenuOpen(true);
    };

    const handleCloseFixedIncomeMenu = () => {
        setFixedIncomeMenuOpen(false);
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
                    <div className="flex space-x-2">
                        <Link to={`/transactions?portfolio_id=${portfolio.id}`} className="btn btn-secondary">
                            View History
                        </Link>
                        <button onClick={handleOpenCreateTransactionModal} className="btn btn-secondary">
                            Add Transaction
                        </button>
                        <div className="relative">
                            <button onClick={handleOpenFixedIncomeMenu} className="btn btn-primary">Add Fixed Income</button>
                            {isFixedIncomeMenuOpen && (
                                <>
                                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10">
                                        <button
                                            onClick={() => {
                                                setAddFixedDepositModalOpen(true);
                                                handleCloseFixedIncomeMenu();
                                            }}
                                            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                        >
                                            Fixed Deposit
                                        </button>
                                        <button
                                            onClick={() => {
                                                setAddBondModalOpen(true);
                                                handleCloseFixedIncomeMenu();
                                            }}
                                            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                        >
                                            Bond
                                        </button>
                                        <button
                                            onClick={() => {
                                                setAddPpfModalOpen(true);
                                                handleCloseFixedIncomeMenu();
                                            }}
                                            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                        >
                                            PPF Account
                                        </button>
                                    </div>
                                    <div onClick={handleCloseFixedIncomeMenu} className="fixed inset-0 z-0"></div>
                                </>
                            )}
                        </div>
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

            <AddFixedDepositModal
                onClose={() => setAddFixedDepositModalOpen(false)}
                isOpen={isAddFixedDepositModalOpen}
                portfolioId={portfolio.id}
            />

            <AddBondModal
                onClose={() => setAddBondModalOpen(false)}
                isOpen={isAddBondModalOpen}
                portfolioId={portfolio.id}
            />

            <AddPPFAccountModal
                onClose={() => setAddPpfModalOpen(false)}
                isOpen={isAddPpfModalOpen}
                portfolioId={portfolio.id}
            />

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