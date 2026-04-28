import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { usePortfolio, usePortfolioAnalytics, usePortfolioSummary, usePortfolioHoldings, useDeleteTransaction, useDeleteBond } from '../../hooks/usePortfolios';
import { useDeleteFixedDeposit } from '../../hooks/useFixedDeposits';
import { useDeleteRecurringDeposit } from '../../hooks/useRecurringDeposits';
import TransactionFormModal from '../../components/Portfolio/TransactionFormModal';
import AddAwardModal from '../../components/Portfolio/AddAwardModal';
import AnalyticsCard from '../../components/Portfolio/AnalyticsCard';
import PortfolioSummary from '../../components/Portfolio/PortfolioSummary';
import HoldingsTable from '../../components/Portfolio/HoldingsTable';
import PpfHoldingDetailModal from '../../components/Portfolio/PpfHoldingDetailModal';
import { Holding } from '../../types/holding';
import BondDetailModal from '../../components/Portfolio/BondDetailModal';
import { Transaction, FixedDepositDetails } from '../../types/portfolio';
import HoldingDetailModal from '../../components/Portfolio/HoldingDetailModal';
import FixedDepositDetailModal from '../../components/Portfolio/FixedDepositDetailModal';
import RecurringDepositDetailModal from '../../components/Portfolio/RecurringDepositDetailModal';
import { DeleteConfirmationModal } from '../../components/common/DeleteConfirmationModal';
import DiversificationCharts from '../../components/Portfolio/DiversificationCharts';
import BenchmarkComparison from '../../components/Portfolio/BenchmarkComparison';
import { RecurringDepositDetails } from '../../types/recurring_deposit';

const PortfolioDetailPage: React.FC = () => {
    const { id: portfolioId } = useParams<{ id: string }>();

    const { data: portfolio, isLoading, isError, error } = usePortfolio(portfolioId);
    const { data: summary, isLoading: isSummaryLoading, error: summaryError } = usePortfolioSummary(portfolioId);
    const { data: holdings, isLoading: isHoldingsLoading, error: holdingsError } = usePortfolioHoldings(portfolioId);
    const { data: analytics, isLoading: isAnalyticsLoading, error: analyticsError } = usePortfolioAnalytics(portfolioId);
    const deleteTransactionMutation = useDeleteTransaction();
    const deleteBondMutation = useDeleteBond();
    const deleteFixedDepositMutation = useDeleteFixedDeposit();
    const deleteRecurringDepositMutation = useDeleteRecurringDeposit();

    const [isTransactionFormOpen, setTransactionFormOpen] = useState(false);
    const [isAddAwardModalOpen, setAddAwardModalOpen] = useState(false);
    const [isAddDropdownOpen, setAddDropdownOpen] = useState(false);
    const [selectedHolding, setSelectedHolding] = useState<Holding | null>(null);
    const [transactionToEdit, setTransactionToEdit] = useState<Transaction | undefined>(undefined);
    const [fdToEdit, setFdToEdit] = useState<FixedDepositDetails | null>(null);
    const [rdToEdit, setRdToEdit] = useState<RecurringDepositDetails | null>(null);
    const [transactionToDelete, setTransactionToDelete] = useState<Transaction | null>(null);
    const [fdToDelete, setFdToDelete] = useState<Holding | null>(null);
    const [bondToDelete, setBondToDelete] = useState<Holding | null>(null);
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

    // Memoize the handler to prevent re-rendering HoldingsTable when other state changes
    const handleHoldingClick = useCallback((holding: Holding) => {
        setSelectedHolding(holding);
    }, []);

    if (isLoading) return <div className="text-center p-8">Loading portfolio details...</div>;
    if (isError) return <div className="text-center p-8 text-red-500">Error: {error.message}</div>;
    if (!portfolio) return <div className="text-center p-8">Portfolio not found.</div>;

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
        setFdToEdit(null);
        setRdToEdit(null);
        setTransactionFormOpen(false);
    };

    const handleCloseAddAwardModal = () => {
        setAddAwardModalOpen(false);
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
        if (bondToDelete && portfolioId) {
            deleteBondMutation.mutate({ portfolioId, bondId: bondToDelete.asset_id }, {
                onSuccess: () => setBondToDelete(null),
                onSettled: handleCloseDetailModal,
            });
        }
    };

    return (
        <div>
            <div className="mb-8">
                <Link to="/portfolios" className="text-blue-600 hover:underline text-sm dark:text-blue-400">
                    &larr; Back to Portfolios
                </Link>
                <div className="flex justify-between items-center mt-2">
                    <h1 className="text-3xl font-bold">{portfolio.name}</h1>
                    <div className="flex space-x-2">
                        <Link to={`/transactions?portfolio_id=${portfolio.id}`} className="btn btn-secondary">
                            View History
                        </Link>
                        <div className="relative inline-flex rounded-md shadow-sm">
                            <button
                                type="button"
                                onClick={handleOpenCreateTransactionModal}
                                className="btn btn-primary rounded-r-none border-r border-blue-600 focus:z-10"
                            >
                                Add Transaction
                            </button>
                            <button
                                type="button"
                                onClick={() => setAddDropdownOpen(!isAddDropdownOpen)}
                                className="btn btn-primary rounded-l-none px-2 focus:z-10"
                                aria-label="Additional actions"
                                aria-expanded={isAddDropdownOpen}
                                aria-haspopup="true"
                            >
                                <span className="text-xs">▼</span>
                            </button>
                            {isAddDropdownOpen && (
                                <>
                                    <div className="fixed inset-0 z-10" onClick={() => setAddDropdownOpen(false)}></div>
                                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-20 border border-gray-200 top-full dark:bg-gray-800 dark:border-gray-700">
                                        <button
                                            onClick={() => { setAddAwardModalOpen(true); setAddDropdownOpen(false); }}
                                            className="block w-full text-left px-4 py-2 hover:bg-gray-100 text-sm text-gray-700 dark:text-gray-300 dark:hover:bg-gray-700"
                                        >
                                            Add ESPP/RSU Award
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </div>
                <p className="text-gray-600 dark:text-gray-400 mt-1">{portfolio.description}</p>
            </div>

            <PortfolioSummary summary={summary} isLoading={isSummaryLoading} error={summaryError} />

            <AnalyticsCard analytics={analytics} isLoading={isAnalyticsLoading} error={analyticsError} />

            <div className="mt-8">
                <DiversificationCharts portfolioId={portfolio.id} />
                <BenchmarkComparison portfolioId={portfolio.id} />
            </div>

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
                    fixedDepositToEdit={fdToEdit || undefined}
                    recurringDepositToEdit={rdToEdit || undefined}
                />
            )}

            {isAddAwardModalOpen && (
                <AddAwardModal
                    onClose={handleCloseAddAwardModal}
                    isOpen={isAddAwardModalOpen}
                    portfolioId={portfolio.id}
                />
            )}

            {selectedHolding && !isTransactionFormOpen && !transactionToDelete && !rdToDelete && !bondToDelete && (
                <>
                    {selectedHolding.asset_type === 'PPF' ? (
                        <PpfHoldingDetailModal
                            isOpen={!!selectedHolding}
                            holding={selectedHolding}
                            portfolioId={portfolio.id}
                            onClose={handleCloseDetailModal}
                            onEdit={handleOpenEditTransactionModal}
                            onDelete={handleOpenDeleteModal}
                        />
                    ) : selectedHolding.asset_type === 'FIXED_DEPOSIT' ? (
                        <FixedDepositDetailModal
                            holding={selectedHolding}
                            onClose={handleCloseDetailModal}
                            onEdit={(details) => {
                                setFdToEdit(details);
                                handleCloseDetailModal();
                                handleOpenCreateTransactionModal();
                            }}
                            onDelete={() => setFdToDelete(selectedHolding)}
                        />
                    ) : selectedHolding.asset_type === 'RECURRING_DEPOSIT' ? (
                        <RecurringDepositDetailModal
                            holding={selectedHolding}
                            onClose={handleCloseDetailModal}
                            onEdit={(details) => {
                                setRdToEdit(details);
                                handleCloseDetailModal();
                                handleOpenCreateTransactionModal();
                            }}
                            onDelete={() => setRdToDelete(selectedHolding)}
                        />
                    ) : selectedHolding.asset_type === 'BOND' ? (
                        <BondDetailModal
                            holding={selectedHolding}
                            portfolioId={portfolio.id}
                            onClose={handleCloseDetailModal}
                            onEditTransaction={handleOpenEditTransactionModal}
                            onDeleteTransaction={handleOpenDeleteModal}
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

            {(transactionToDelete || fdToDelete || rdToDelete || bondToDelete) && (
                <DeleteConfirmationModal
                    isOpen={!!transactionToDelete || !!fdToDelete || !!rdToDelete || !!bondToDelete}
                    onClose={() => {
                        setTransactionToDelete(null);
                        setFdToDelete(null);
                        setRdToDelete(null);
                        setBondToDelete(null);
                    }}
                    onConfirm={handleConfirmDelete}
                    title={fdToDelete ? "Delete Fixed Deposit" : rdToDelete ? "Delete Recurring Deposit" : "Delete Transaction"}
                    message={
                        fdToDelete
                            ? `Are you sure you want to delete the FD "${fdToDelete.asset_name}"? This action cannot be undone.`
                            : rdToDelete
                                ? `Are you sure you want to delete the RD "${rdToDelete.asset_name}"? This action cannot be undone.`
                                : bondToDelete
                                    ? `Are you sure you want to delete the bond "${bondToDelete.asset_name}" and all its transactions? This action cannot be undone.`
                                    : `Are you sure you want to delete this ${transactionToDelete?.transaction_type} transaction of ${Number(transactionToDelete?.quantity).toLocaleString()} units? This action cannot be undone.`
                    }
                    isDeleting={deleteTransactionMutation.isPending || deleteFixedDepositMutation.isPending || deleteRecurringDepositMutation.isPending || deleteBondMutation.isPending}
                />
            )}
        </div>
    );
};

export default PortfolioDetailPage;
