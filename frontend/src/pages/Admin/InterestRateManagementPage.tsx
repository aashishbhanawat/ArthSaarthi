import React, { useState } from 'react';
import { useInterestRates, useDeleteInterestRate } from '../../hooks/useInterestRates';
import { useQueryClient } from '@tanstack/react-query';
import InterestRateTable from '../../components/Admin/InterestRateTable';
import InterestRateFormModal from '../../components/Admin/InterestRateFormModal';
import { DeleteConfirmationModal } from '../../components/common/DeleteConfirmationModal';
import { HistoricalInterestRate } from '../../types/interestRate';
import { useToast } from '../../context/ToastContext';

const InterestRateManagementPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const deleteMutation = useDeleteInterestRate();

  const { data: rates = [], isLoading, isError } = useInterestRates();
  const [isFormModalOpen, setFormModalOpen] = useState(false);
  const [isDeleteModalOpen, setDeleteModalOpen] = useState(false);
  const [rateToEdit, setRateToEdit] = useState<HistoricalInterestRate | null>(null);
  const [rateToDelete, setRateToDelete] = useState<HistoricalInterestRate | null>(null);

  const handleOpenCreateModal = () => {
    setRateToEdit(null);
    setFormModalOpen(true);
  };

  const handleOpenEditModal = (rate: HistoricalInterestRate) => {
    setRateToEdit(rate);
    setFormModalOpen(true);
  };

  const handleOpenDeleteModal = (rate: HistoricalInterestRate) => {
    setRateToDelete(rate);
    setDeleteModalOpen(true);
  };

  const handleConfirmDelete = () => {
    if (rateToDelete) {
      deleteMutation.mutate(rateToDelete.id, {
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['interestRates'] });
          setDeleteModalOpen(false);
          setRateToDelete(null);
        },
        onError: () => {
          addToast('Failed to delete interest rate.', 'error');
        },
      });
    }
  };

  const sortedRates = [...rates].sort((a, b) => new Date(b.start_date).getTime() - new Date(a.start_date).getTime());

  return (
    <div className="container mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Interest Rate Management</h1>
        <button onClick={handleOpenCreateModal} className="btn btn-primary">
          Add New Rate
        </button>
      </div>

      {isLoading && <p>Loading interest rates...</p>}
      {isError && <p className="text-red-500">Error fetching interest rates.</p>}
      {!isLoading && !isError && (
        <div className="card">
          <InterestRateTable rates={sortedRates} onEdit={handleOpenEditModal} onDelete={handleOpenDeleteModal} />
        </div>
      )}

      <InterestRateFormModal isOpen={isFormModalOpen} onClose={() => setFormModalOpen(false)} rateToEdit={rateToEdit} />

      {rateToDelete && (
        <DeleteConfirmationModal isOpen={isDeleteModalOpen} onClose={() => setDeleteModalOpen(false)} onConfirm={handleConfirmDelete} title="Delete Interest Rate" message={`Are you sure you want to delete the rate for ${rateToDelete.scheme_name} starting ${rateToDelete.start_date}?`} isDeleting={deleteMutation.isPending} />
      )}
    </div>
  );
};

export default InterestRateManagementPage;