import React, { useState } from 'react';
import { Goal } from '../../types/goal';
import GoalDetailView from './GoalDetailView';
import { Button } from 'src/components/ui/button';
import { LinkIcon, TrashIcon } from '@heroicons/react/24/outline';
import ConfirmationModal from '../common/DeleteConfirmationModal';

interface GoalCardProps {
  goal: Goal;
  onLinkAsset: (goalId: string) => void;
  onDelete: (goalId: string) => void;
}

const GoalCard: React.FC<GoalCardProps> = ({ goal, onLinkAsset, onDelete }) => {
  const [isDetailsVisible, setIsDetailsVisible] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  const handleDelete = () => {
    setIsDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    onDelete(goal.id);
    setIsDeleteDialogOpen(false);
  };

  return (
    <div className="bg-white shadow rounded-lg p-4 mb-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">{goal.name}</h2>
        <div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsDetailsVisible(!isDetailsVisible)}
            className="mr-2"
            data-testid={`goal-details-button-${goal.id}`}
          >
            {isDetailsVisible ? 'Hide Details' : 'Show Details'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onLinkAsset(goal.id)}
            disabled={!goal.id}
            data-testid={`link-asset-button-${goal.id}`}
          >
            <LinkIcon className="h-4 w-4 mr-2" />
            Link Asset
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleDelete}
            className="ml-2"
            data-testid={`delete-goal-button-${goal.id}`}
          >
            <TrashIcon className="h-4 w-4 mr-2" />
            Delete
          </Button>
        </div>
      </div>
      {isDetailsVisible && <GoalDetailView goal={goal} />}
      <ConfirmationModal
        isOpen={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        onConfirm={confirmDelete}
        title="Delete Goal"
        message={`Are you sure you want to delete the goal "${goal.name}"? This action cannot be undone.`}
      />
    </div>
  );
};

export default GoalCard;
