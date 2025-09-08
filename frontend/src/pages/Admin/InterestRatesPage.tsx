import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { getInterestRates, createInterestRate, updateInterestRate, deleteInterestRate } from '../../services/adminApi';
import { HistoricalInterestRate } from '../../types/asset';
import InterestRatesTable from '../../components/Admin/InterestRatesTable';
import InterestRateFormModal from '../../components/Admin/InterestRateFormModal';
import { PlusIcon } from '@heroicons/react/24/solid';

const InterestRatesPage: React.FC = () => {
    const queryClient = useQueryClient();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [rateToEdit, setRateToEdit] = useState<HistoricalInterestRate | undefined>(undefined);

    const { data: rates, isLoading, isError } = useQuery('interestRates', getInterestRates);

    const createRateMutation = useMutation(createInterestRate, {
        onSuccess: () => {
            queryClient.invalidateQueries('interestRates');
            setIsModalOpen(false);
        },
    });

    const updateRateMutation = useMutation(updateInterestRate, {
        onSuccess: () => {
            queryClient.invalidateQueries('interestRates');
            setIsModalOpen(false);
            setRateToEdit(undefined);
        },
    });

    const deleteRateMutation = useMutation(deleteInterestRate, {
        onSuccess: () => {
            queryClient.invalidateQueries('interestRates');
        },
    });

    const handleOpenModal = (rate?: HistoricalInterestRate) => {
        setRateToEdit(rate);
        setIsModalOpen(true);
    };

    const handleCloseModal = () => {
        setIsModalOpen(false);
        setRateToEdit(undefined);
    };

    const handleDelete = (rateId: string) => {
        if (window.confirm('Are you sure you want to delete this interest rate?')) {
            deleteRateMutation.mutate(rateId);
        }
    };

    return (
        <div className="container mx-auto p-4">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold">Manage Interest Rates</h1>
                <button onClick={() => handleOpenModal()} className="btn btn-primary inline-flex items-center">
                    <PlusIcon className="h-5 w-5 mr-2" />
                    Add Rate
                </button>
            </div>

            {isLoading && <p>Loading interest rates...</p>}
            {isError && <p className="text-red-500">Error fetching interest rates.</p>}
            {rates && <InterestRatesTable rates={rates} onEdit={handleOpenModal} onDelete={handleDelete} />}

            {isModalOpen && (
                <InterestRateFormModal
                    isOpen={isModalOpen}
                    onClose={handleCloseModal}
                    onSubmit={(data) => {
                        if (rateToEdit) {
                            updateRateMutation.mutate({ rateId: rateToEdit.id, data });
                        } else {
                            createRateMutation.mutate(data);
                        }
                    }}
                    initialData={rateToEdit}
                />
            )}
        </div>
    );
};

export default InterestRatesPage;
