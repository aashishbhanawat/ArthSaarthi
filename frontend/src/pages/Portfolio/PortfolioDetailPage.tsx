import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { usePortfolio, usePortfolioAnalytics, useDeleteTransaction } from '../../hooks/usePortfolios';
import TransactionList from '../../components/Portfolio/TransactionList';
import TransactionFormModal from '../../components/Portfolio/TransactionFormModal';
import { DeleteConfirmationModal } from '../../components/common/DeleteConfirmationModal';
import AnalyticsCard from '../../components/Portfolio/AnalyticsCard';
import { Transaction } from '../../types/portfolio';

const PortfolioDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();

    const { data: portfolio, isLoading, isError, error } = usePortfolio(id);
    const { data: analytics, isLoading: isAnalyticsLoading, error: analyticsError } = usePortfolioAnalytics(id);
    const deleteTransactionMutation = useDeleteTransaction();

    const [isTransactionFormOpen, setTransactionFormOpen] = useState(false);
    const [transactionToEdit, setTransactionToEdit] = useState<Transaction | null>(null);

    const [isDeleteModalOpen, setDeleteModalOpen] = useState(false);
    const [transactionToDelete, setTransactionToDelete] = useState<Transaction | null>(null);

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
                    <button onClick={() => {
                        setTransactionToEdit(null);
                        setTransactionFormOpen(true);
                    }} className="btn btn-primary">
                        Add Transaction
                    </button>
                </div>
            </div>

            <AnalyticsCard analytics={analytics} isLoading={isAnalyticsLoading} error={analyticsError} />

            <div className="mt-8">
                <TransactionList
                    transactions={portfolio.transactions || []}
                    onEdit={(transaction) => {
                        setTransactionToEdit(transaction);
                        setTransactionFormOpen(true);
                    }}
                    onDelete={(transaction) => {
                        setTransactionToDelete(transaction);
                        setDeleteModalOpen(true);
                    }}
                />
            </div>

            {isTransactionFormOpen && (
                <TransactionFormModal
                    onClose={() => setTransactionFormOpen(false)}
                    portfolioId={portfolio.id}
                    transactionToEdit={transactionToEdit || undefined}
                />
            )}

            {isDeleteModalOpen && transactionToDelete && (
                <DeleteConfirmationModal
                    isOpen={isDeleteModalOpen}
                    onClose={() => setDeleteModalOpen(false)}
                    onConfirm={() => {
                        if (transactionToDelete) {
                            deleteTransactionMutation.mutate(
                                { portfolioId: portfolio.id, transactionId: transactionToDelete.id },
                                { onSuccess: () => setDeleteModalOpen(false) }
                            );
                        }
                    }}
                    title="Delete Transaction"
                    message={
                        <p>
                            Are you sure you want to delete this transaction?
                            <br />
                            <span className="font-semibold">{transactionToDelete.asset.ticker_symbol} - {transactionToDelete.transaction_type} - {transactionToDelete.quantity} units</span>
                        </p>
                    }
                    isDeleting={deleteTransactionMutation.isPending}
                />
            )}
        </div>
    );
};

export default PortfolioDetailPage;