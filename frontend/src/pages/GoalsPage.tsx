import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getGoals, createGoal, deleteGoal, linkAssetToGoal } from '../services/goalApi';
import { getPortfolios } from '../services/portfolioApi';
import { Goal } from '../types/goal';
import { Portfolio } from '../types/portfolio';
import { Asset } from '../types/asset';
import { Button } from '@/components/common/Button';
import { PlusIcon } from '@heroicons/react/24/outline';
import GoalCard from '../components/Goals/GoalCard';
import GoalFormModal from '../components/modals/GoalFormModal';
import AssetLinkModal from '../components/modals/AssetLinkModal';
import { getAssets } from '@/services/assetApi';
import ConfirmationModal from '../components/common/DeleteConfirmationModal';

const GoalsPage = () => {
    const queryClient = useQueryClient();
    const [isCreateModalOpen, setCreateModalOpen] = useState(false);
    const [isLinkModalOpen, setLinkModalOpen] = useState(false);
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
    const [selectedGoalId, setSelectedGoalId] = useState<string | null>(null);

    const { data: goals, isLoading, isError } = useQuery<Goal[], Error>({
        queryKey: ['goals'],
        queryFn: getGoals,
    });

    const { data: portfolios } = useQuery<Portfolio[], Error>({
        queryKey: ['portfolios'],
        queryFn: getPortfolios,
    });

    const { data: assets } = useQuery<Asset[], Error>({
        queryKey: ['assets'],
        queryFn: getAssets,
    });

    const createMutation = useMutation({
        mutationFn: createGoal,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['goals'] });
            setCreateModalOpen(false);
        },
    });

    const deleteMutation = useMutation({
        mutationFn: deleteGoal,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['goals'] });
            setIsDeleteDialogOpen(false);
        },
    });

    const linkAssetMutation = useMutation({
        mutationFn: (data: { goalId: string; assetId: string; assetType: 'portfolio' | 'asset' }) =>
            linkAssetToGoal(data.goalId, data.assetId, data.assetType),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['goals'] });
            setLinkModalOpen(false);
        },
    });


    const handleCreateGoal = (goal: Omit<Goal, 'id' | 'user_id' | 'current_value' | 'progress' | 'linked_assets'>) => {
        createMutation.mutate(goal);
    };

    const handleDelete = (goalId: string) => {
        setSelectedGoalId(goalId);
        setIsDeleteDialogOpen(true);
    };

    const confirmDelete = () => {
        if (selectedGoalId) {
            deleteMutation.mutate(selectedGoalId);
        }
    };

    const handleLinkAsset = (goalId: string) => {
        setSelectedGoalId(goalId);
        setLinkModalOpen(true);
    };

    const handleConfirmLink = (assetId: string, assetType: 'portfolio' | 'asset') => {
        if (selectedGoalId) {
            linkAssetMutation.mutate({ goalId: selectedGoalId, assetId, assetType });
        }
    };

    if (isLoading) return <div>Loading goals...</div>;
    if (isError) return <div>Error fetching goals</div>;

    return (
        <div className="container mx-auto p-4">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold">Financial Goals</h1>
                <Button onClick={() => setCreateModalOpen(true)}>
                    <PlusIcon className="h-5 w-5 mr-2" />
                    Create New Goal
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {goals?.map((goal) => (
                    <GoalCard key={goal.id} goal={goal} onLinkAsset={handleLinkAsset} onDelete={handleDelete} />
                ))}
            </div>

            <GoalFormModal
                isOpen={isCreateModalOpen}
                onClose={() => setCreateModalOpen(false)}
                onSubmit={handleCreateGoal}
            />

            {isLinkModalOpen && selectedGoalId && (
                <AssetLinkModal
                    isOpen={isLinkModalOpen}
                    onClose={() => setLinkModalOpen(false)}
                    onLink={handleConfirmLink}
                    portfolios={portfolios || []}
                    assets={assets || []}
                />
            )}

            {isDeleteDialogOpen && (
                <ConfirmationModal
                    isOpen={isDeleteDialogOpen}
                    onClose={() => setIsDeleteDialogOpen(false)}
                    onConfirm={confirmDelete}
                    title="Delete Goal"
                    message={`Are you sure you want to delete this goal "${goals?.find(g => g.id === selectedGoalId)?.name}"? This action cannot be undone.`}
                />
            )}
        </div>
    );
};

export default GoalsPage;
