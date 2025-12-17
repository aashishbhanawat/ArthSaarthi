import React, { useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useTransactions } from '../hooks/useTransactions';
import TransactionFilterBar from '../components/Transactions/TransactionFilterBar';
import TransactionHistoryTable from '../components/Transactions/TransactionHistoryTable';
import PaginationControls from '../components/common/PaginationControls';
import TransactionFormModal from '../components/Portfolio/TransactionFormModal';
import { DeleteConfirmationModal } from '../components/common/DeleteConfirmationModal';
import { Transaction } from '../types/portfolio';
import { useDeleteTransaction } from '../hooks/useTransactions';

const PAGE_SIZE = 15;

const TransactionsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const [transactionToEdit, setTransactionToEdit] = useState<Transaction | null>(null);
  const [transactionToDelete, setTransactionToDelete] = useState<Transaction | null>(null);

  // State for modals
  const deleteTransactionMutation = useDeleteTransaction();


  // Filters state derived from URL search params
  const filters = useMemo(() => {
    const page = parseInt(searchParams.get('page') || '0', 10);
    return {
      portfolio_id: searchParams.get('portfolio_id') || undefined,
      asset_id: searchParams.get('asset_id') || undefined,
      transaction_type: searchParams.get('transaction_type') || undefined,
      start_date: searchParams.get('start_date') || undefined,
      end_date: searchParams.get('end_date') || undefined,
      skip: page * PAGE_SIZE,
      limit: PAGE_SIZE,
    };
  }, [searchParams]);

  // cast data to any or specific response type because useTransactions might return something else?
  // useTransactions returns TransactionsResponse which has transactions: Transaction[].
  // But if types/transaction.ts Transaction is different from types/portfolio.ts Transaction, there is mismatch.
  // I updated useTransactions in usePortfolios.ts (which is seemingly where it should be, but here it imports from ../hooks/useTransactions).
  // Wait, useTransactions is imported from `../hooks/useTransactions`.
  // I updated `usePortfolios.ts` but `TransactionsPage` imports from `useTransactions.ts`?
  // Let's check `frontend/src/hooks/useTransactions.ts`.
  const { data, isLoading, isError, error } = useTransactions(filters);

  const handlePageChange = (newPage: number) => {
    setSearchParams((prev) => {
      prev.set('page', newPage.toString());
      return prev;
    });
  };

  const handleEdit = (transaction: Transaction) => {
    setTransactionToEdit(transaction);
  };

  const handleDelete = (transaction: Transaction) => {
    setTransactionToDelete(transaction);
  };

  const handleConfirmDelete = () => {
    if (transactionToDelete) {
      deleteTransactionMutation.mutate(
        { portfolioId: transactionToDelete.portfolio_id, transactionId: transactionToDelete.id },
        {
          onSuccess: () => {
            setTransactionToDelete(null);
            queryClient.invalidateQueries({ queryKey: ['transactions'] });
          },
        }
      );
    }
  };

  const handleCloseFormModal = () => {
    setTransactionToEdit(null);
    // Invalidate queries on close to reflect any potential updates
    queryClient.invalidateQueries({ queryKey: ['transactions'] });
  };


  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Transaction History</h1>
      <TransactionFilterBar />

      {isLoading && <div className="text-center p-8">Loading transactions...</div>}
      {isError && <div className="text-center p-8 text-red-500">Error: {(error as Error).message}</div>}
      {data && data.transactions && (
        (() => {
          const pageCount = Math.ceil(data.total / PAGE_SIZE);
          const currentPage = (filters.skip || 0) / PAGE_SIZE;
          return (
            <>
              <TransactionHistoryTable transactions={data.transactions} onEdit={handleEdit} onDelete={handleDelete} />
              {pageCount > 1 && (
                <PaginationControls currentPage={currentPage} pageCount={pageCount} onPageChange={handlePageChange} />
              )}
            </>
          );
        })()
      )}

      {transactionToEdit && (
        <TransactionFormModal
          isOpen={!!transactionToEdit}
          onClose={handleCloseFormModal}
          portfolioId={transactionToEdit.portfolio_id}
          transactionToEdit={transactionToEdit}
        />
      )}

      {transactionToDelete && (
        <DeleteConfirmationModal
          isOpen={!!transactionToDelete}
          onClose={() => setTransactionToDelete(null)}
          onConfirm={handleConfirmDelete}
          title="Delete Transaction"
          message={`Are you sure you want to delete this transaction? This action cannot be undone.`}
          isDeleting={deleteTransactionMutation.isPending}
        />
      )}
    </div>
  );
};

export default TransactionsPage;
